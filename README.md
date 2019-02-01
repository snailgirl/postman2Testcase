# postman2Testcase
将 postman json 文件转换为 HttpRunner YAML/JSON 用例

## 用法

```shell
1.运行 app.py
2.通过 http://127.0.0.1:5000/index 访问
```

## postman 断言
将 postman 断言添加至用例中，但目前只支持以下 2 种断言方法，断言需具体到字段

```
案例一:
var jsonData = pm.response.json();
pm.test("检查Response Body 是否包含'hello'字符串", function () {
    pm.expect(jsonData.responseBody.resultList[0].name).to.eql("hello");
});

案例二：
var data = JSON.parse(responseBody);
tests["字段返回是否hello"] = data.responseBody.resultList[0].name === "hello"; 

```

