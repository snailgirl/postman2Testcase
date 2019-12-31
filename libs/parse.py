import json
import os
import re
from ruamel import yaml

class HpptrunnerCase():
    def __init__(self):
        # 存储用例
        self.json_case = []

    def get_postman_json(self):
        '''
        获取postman json 文件
        :return:
        '''
        with open(self.input_file, 'rb') as f:
            postman_json = json.loads(f.read().decode('utf-8'))
        return postman_json

    def create_case_file(self, input_file, output_yaml_file_name):
        # postman json文件路径
        self.input_file = input_file
        # 获取postman json 文件
        postman_json = self.get_postman_json()
        # 获取处理过的 json 用例
        json_case = self.get_json_case(postman_json)
        # 生成用例文件名
        self.output_filename = output_yaml_file_name
        # 写入文件
        my_json_str = json.dumps(json_case, ensure_ascii=False, indent=4)
        if isinstance(my_json_str, bytes):
            my_json_str = my_json_str.decode("utf-8")
        # 保存json 用例
        if self.output_filename.endswith('.json'):
            with open(self.output_filename, 'w', encoding="utf-8") as outfile:
                outfile.write(my_json_str)
        # 保存yaml 用例
        if self.output_filename.endswith('.yaml'):
            with open(self.output_filename, 'w', encoding='utf-8') as outfile:
                yaml.dump(json.loads(my_json_str), outfile, allow_unicode=True, Dumper=yaml.RoundTripDumper, indent=4)

    def get_json_case(self, postman_json):
        for case_item in postman_json.get('item'):
            if 'item' in case_item:
                self.get_json_case(case_item)
            else:
                testcase = self.get_each_case(case_item)
                # 存储json用例
                self.json_case.append(testcase)
        return self.json_case

    def get_each_case(self, item):
        """ parse each item in postman to testcase in httprunner
        """
        testcase_test={}
        testcase_test['test'] = {}
        testcase = testcase_test['test']
        testcase["name"] = item["name"]
        # testcase["def"] = item["name"]
        testcase["validate"] = []
        testcase["variables"] = []
        testcase["extract"]=[]
        testcase["validate"] = []

        # variables、validate和extract字段内容
        validate_list = []
        testcase["validate"].append({'eq': ['status_code', 200]})
        if 'event' in item:
            event_res = self.get_event_content(item['event'])
            # testcase["variables"]
            if event_res[0]:
                for res_item in event_res[0].items():
                    testcase["variables"].append({res_item[0]: self.parse_value_from_type(res_item[1])})
                    validate_list.append(res_item[0])
            if event_res[1]:
                for res_item in event_res[1].items():
                    testcase["validate"].append({'eq': [res_item[0], self.parse_value_from_type(res_item[1])]})
            if event_res[2]:
                for res_item in event_res[2].items():
                    testcase["extract"].append({res_item[0]: self.parse_value_from_type(res_item[1])})

        # request 字段内容
        request = {}
        request["method"] = item["request"]["method"]

        url = ""
        if isinstance(item["request"]["url"], str):
            url = item["request"]["url"]
        elif isinstance(item["request"]["url"], dict):
            if "raw" in item["request"]["url"].keys():
                url= item["request"]["url"]["raw"]

        if request["method"] in ["POST", "PUT"]:
            request["url"] = url.replace("{{", "$").replace("}}", "")

            headers = {}
            for header in item["request"]["header"]:
                headers[header["key"]] = header["value"].replace("{{", "$").replace("}}", "")
            request["headers"] = headers

            body = {}
            # 处理body参数添加至testcase['variables']
            def get_varia_parm(list_item):
                for param in list_item.items():
                    if isinstance(param[1], (list, dict)):
                        if param[0] not in validate_list:
                            testcase['variables'].append({param[0]: param[1]})
                            validate_list.append(param[0])
                    else:
                        if param[0] not in validate_list:
                            testcase['variables'].append({param[0]: self.parse_value_from_type(param[1])})
                            validate_list.append(param[0])
                    body[param[0]] = '$' + param[0]
            if item["request"]["body"] != {}:
                mode = item["request"]["body"]["mode"]
                mode_body = str(item["request"]["body"][mode])
                # 处理{{param}}参数
                mode_body = self.get_param(mode_body)
                if mode in ['raw']:
                    if mode_body:
                        mode_body_new = json.loads(mode_body)
                        if isinstance(mode_body_new, dict):
                            # 处理body参数添加至testcase['variables']
                            get_varia_parm(mode_body_new)
                        elif isinstance(mode_body_new, list):
                            for list_item in mode_body_new:
                                # 处理body参数添加至testcase['variables']
                                get_varia_parm(list_item)
                            body = [body]
                else:
                    mode_body_new = eval(mode_body)
                    for param in mode_body_new:
                        if 'src' in param:
                            if {param['key']: self.parse_value_from_type(param['src'])} not in testcase['variables'] and param['key'] == 'file':
                                testcase['variables'].append({param['key']: self.parse_value_from_type(param['src'])})
                        elif {param['key']: self.parse_value_from_type(param['value'])} not in testcase['variables']:
                            testcase['variables'].append({param['key']: self.parse_value_from_type(param['value'])})
                        body[param['key']] = '$' + param['key']
            request["json"] = body
        else:
            request["url"] = url.split("?")[0].replace("{{", "$").replace("}}", "")
            headers = {}
            for header in item["request"]["header"]:
                headers[header["key"]] = header["value"].replace("{{", "$").replace("}}", "")
            request["headers"] = headers

            body = {}
            if "query" in item["request"]["url"].keys():
                for query in item["request"]["url"]["query"]:
                    query_value = self.parse_value_from_type(query["value"])
                    if not str(query_value).isdigit():
                        # 处理{{param}}参数
                        query_value = self.get_param(query_value)
                    if query["key"] not in validate_list:
                        testcase["variables"].append({query["key"]: query_value})
                        validate_list.append(query["key"])
                    body[query["key"]] = "$"+query["key"]
            request["params"] = body

        testcase["request"] = request
        # 调整 extract validate 顺序
        extract = testcase.pop('extract')
        testcase['extract'] = extract
        validate = testcase.pop('validate')
        testcase['validate'] = validate
        return testcase_test

    def parse_value_from_type(self, value):
        '''
        处理数据类型
        :param value:
        :return:
        '''
        if isinstance(value, int):
            return int(value)
        elif isinstance(value, float):
            return float(value)
        elif value == None:
            return None
        elif value.lower() == "false":
            return False
        elif value.lower() == "true":
            return True
        else:
            return str(value).strip("'").strip('"')

    def get_param(self, mode_body):
        """
        正则处理{{param}}处理成 $param
        :param mode_body:
        :return:
        """
        # 处理 {{param}}无引号参数
        if isinstance(mode_body,bool):
            return mode_body
        re_str = re.findall('''[^"']{{(\w*)}}[^"]''', mode_body)
        for conver_str in re_str:
            new_str = mode_body.replace('{{' + conver_str + '}}', '"$' + conver_str + '"')
            mode_body = new_str
        # 处理 "{{param}}" 有引号参数
        re_str = re.findall("{{(\w*)}}", mode_body)
        for conver_str in re_str:
            new_str = mode_body.replace('{{' + conver_str + '}}', '$' + conver_str)
            mode_body = new_str
        return mode_body

    def get_event_content(self,event_content):
        """
        event 模块
        :param event_content:
        :return: variables_res把结果添加到test['variables']中,validate_res把结果写入test['validate'], extract_res把结果写入test['extract']
        """
        variables_res = {}
        validate_res = {}
        extract_res = {}

        def get_validate(validate_res, validate_result):
            for result_item in validate_result:
                res_item = result_item[0].replace('[', '.').replace(']', '')
                validate_key = 'content.' + res_item
                # black_list 不保存的断言(黑名单)
                black_list = ['status_code']
                if validate_key not in black_list:
                    validate_value = result_item[1].strip('"')
                    validate_res[validate_key] = validate_value
                    if validate_value.isdigit():
                        validate_res[validate_key] = int(validate_value)
            return validate_res

        if event_content:
            for item in event_content:
                # variables 数据准备
                if item['listen'] == 'prerequest':
                    exec_content = item['script']['exec']
                    for exec_item in exec_content:
                        result = re.findall('.set\("(.*)",(.*)\);', exec_item)
                        if result:
                            for result_item in result:
                                variables_key = result_item[0].strip()
                                variables_value = result_item[1].strip('"').replace("'","").strip()
                                variables_res[variables_key] = variables_value
                                if variables_value.isdigit():
                                    variables_res[variables_key] = int(variables_value)
                # validate 和 extract数据处理
                elif item['listen'] == 'test':
                    exec_content = item['script']['exec']
                    for validate_item in exec_content:
                        # validate 测试结果验证，数据处理
                        validate_result = re.findall('expect\(\w*\.?(.*)\)\.to\.eql\((.*)\)', validate_item.replace(' ', ''))
                        if validate_result:
                            validate_res = get_validate(validate_res, validate_result)
                        validate_result = re.findall('tests\[\"\w*\"\]=\w*\.?(.*)===(.*);',validate_item.replace(' ', ''))
                        if validate_result:
                            validate_res = get_validate(validate_res, validate_result)

                        # extract 保存response指定参数，数据处理
                        extract_result = re.findall('globals.set\(\"(.*)\",\w*\.(.*)\)', validate_item.replace(' ', ''))
                        if extract_result:
                            for extract_item in extract_result:
                                extract_val = 'content.' + extract_item[1].replace('[', '.').replace(']', '')
                                extract_res[extract_item[0]] = extract_val.replace('"', '')
        return variables_res, validate_res, extract_res
