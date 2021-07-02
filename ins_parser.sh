#!/bin/bash
#
# 功能: 专为shell脚本设计的INS配置文件（类ini配置文件）解析器
# 作者: Bingo
# INS示例: 
#__sectionA__()
#{
#    # this is a comment in INS and this section not content key2
#    key1=value1
#}
#__sectionB__()
#{
#    key1=value1
#    key2=hello
#    key3=/home/ubp/aa.log
#    key4="/home /opt /tmp"
#    key6="${key2} $(whoami)"
#}
# INS配置文件需要满足:
#    1. 注释只能以 # 开头，且注释中不能含有 'key='，否则会跟真实的 key=value 冲突
#    2. section 命名只能是字母数字和单下划线组合，不能包含路径和双下划线以及其他特殊字符
#    3. section 格式 __xxx__(), 且需要顶格写
#    4. key=value 三者之间不能有空格
#    5. key=value 组合必须包含在section的一对 {} 中
#    6. key 命名只能是字母数字和下划线组合，不能包含路径以及其他特殊字符
#    7. value 不可为多行（set时不可包含\n），不可包含双引号" ，且含有空格时需要用双引号扩起两端，连续串时可不用双引号
#    8. value 可为有表达式，但不建议使用
#    
# 使用示例: (参见 testcase 函数)
#

G_INS_PATH=''

function load_ins()
{
    [ -f "${1}" ] || { echo "[ERROR] load_ins failed: INS '${1}' is None or not exist" >&2; return 1; }
    source "${1}" &>/dev/null || { echo "[ERROR] load_ini from '${1}' failed" >&2; return 1; }
    G_INS_PATH="${1}"
    sed -i 's/\t/    /g' "${G_INS_PATH}"
    return 0
}

function __check()
{
    [ -f "${G_INS_PATH}" ] || { echo "[ERROR] INS '${G_INS_PATH}' is invalid, need load_ins first" >&2; return 1; }
    return 0
}

function reload_ins()
{
    __check || return 1
    load_ins "${G_INS_PATH}"
    return $?
}

function get_sections()
{
    __check || return 1
    local matchs=$(grep "^__.*()" "${G_INS_PATH}")
    local sections=$(echo "${matchs}" | awk -F"__" '{print $2}')
    echo "${sections}"
    return 0
}

# $1  section
# $2  key
function get_value()
{
    __check || return 1
    __${1}__ &>/dev/null || { echo "[ERROR] '${G_INS_PATH}' load_section '${1}' failed" >&2; return 1; }
    eval "echo \"\$${2}\""
    return 0
}

# $1  section
# $2  key
# $3  value
function set_value()
{
    __check || return 1
    local my_section_line=$(grep -n "^__${1}__()" "${G_INS_PATH}" | cut -d: -f1)
    [ -z "${my_section_line}" ] && { echo "[ERROR] '${G_INS_PATH}' set_value failed: not found section '${1}'" >&2; return 1; }
    local section_lines=$(grep -n "^__.*()" "${G_INS_PATH}" | cut -d: -f1)
    local next_section_line=${my_section_line}
    for line in ${section_lines}
    do
        [ "${line}" -gt "${my_section_line}" ] && { local next_section_line=${line}; break; }
    done
    [ "${next_section_line}" -eq "${my_section_line}" ] && next_section_line=$(expr $(wc -l "${G_INS_PATH}" | cut -d' ' -f1) + 1)
    local match_lines=$(grep -n -w "${2}" "${G_INS_PATH}" | grep "${2}=" | cut -d: -f1)
    local _got='F'
    for line in ${match_lines}
    do
        [ "${line}" -gt "${my_section_line}" -a "${line}" -lt "${next_section_line}" ] && { local _got='T'; break; }
    done
    [ "${_got}" = "F" ] && { echo "[ERROR] '${G_INS_PATH}' set_value failed: '${2}' not found in section '${1}'" >&2; return 1; }
    sed -i "${line}a\    ${2}=\"${3}\"" "${G_INS_PATH}" || { echo "[ERROR] '${G_INS_PATH}' set_value failed: append failed" >&2; return 1; }
    sed -i "${line}d" "${G_INS_PATH}" || { echo "[ERROR] '${G_INS_PATH}' set_value failed: delete failed" >&2; return 1; }
    return 0
}

function testcase()
{
    cat <<COMMENT > test.ins
__sectionA__()
{
    key1=value1
}

__sectionB__()
{
    key1=value1
    key2=value2
}
__sectionC__()
{
    file=/home/ubp/aa.log
    paths="/home /opt /tmp"
    user="hello \$(whoami), paths is \${paths}"
}
COMMENT

    # load INS
    load_ins "test.ins"

    # get sections
    echo "get_sections:"
    get_sections
    
    # get value
    echo "get_value sectionA key2: $(get_value sectionA key2)"
    echo "get_value sectionB key2: $(get_value sectionB key2)"
    echo "get_value sectionC file: $(get_value sectionC file)"
    echo "get_value sectionC paths: $(get_value sectionC paths)"
    echo "get_value sectionC user: $(get_value sectionC user)"
    
    # set value, result: true
    set_value sectionB key2 B-value2
    echo "(ret=$?) set_value sectionB key2 B-value2"
	set_value sectionC paths "A B C D"
	echo "(ret=$?) set_value sectionC paths 'A B C D'"
	
	# set value, result: false
    set_value sectionA key2 A-value2
    echo "(ret=$?) set_value sectionA key2 A-value2"
	
	reload_ins
    echo "get_value sectionA key2: $(get_value sectionA key2)"
    echo "get_value sectionB key2: $(get_value sectionB key2)"
    echo "get_value sectionC file: $(get_value sectionC file)"
    echo "get_value sectionC paths: $(get_value sectionC paths)"
    echo "get_value sectionC user: $(get_value sectionC user)"

    return 0
}

# testcase

