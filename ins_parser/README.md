# INS Parser
__专为shell脚本设计的INS配置文件（类ini配置文件）解析器__

> INS 配置文件示例:
```
__sectionA__()
{
    # this is a comment in INS and this section not content key2
    key1=value1
}
__sectionB__()
{
    key1=value1
    key2=hello
    key3=/home/ubp/aa.log
    key4="/home /opt /tmp"
    key6="${key2} $(whoami)"
}
```
> INS配置文件需要满足:
- 注释只能以 # 开头，且注释中不能含有 'key='，否则会跟真实的 key=value 冲突
- section 命名只能是字母数字和单下划线组合，不能包含路径和双下划线以及其他特殊字符
- section 格式 \_\_xxx__(), 且需要顶格写
- key=value 三者之间不能有空格
- key=value 组合必须包含在section的一对 {} 中
- key 命名只能是字母数字和下划线组合，不能包含路径以及其他特殊字符
- value 不可为多行（set时不可包含\n），不可包含双引号" ，且含有空格时需要用双引号扩起两端，连续串时可不用双引号
- value 可为有表达式，但不建议使用
