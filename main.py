from libs.parse import *

def get_case(postman_testset_file, output_yaml_file_name):
    newcase = HpptrunnerCase()
    newcase.create_case_file(postman_testset_file, output_yaml_file_name)

if __name__ == '__main__':
   get_case(r'D:\code_projects\test_code\postman2Testcase\data\postman_医馆中心(开发测试)postman.json',
                            r'D:\code_projects\test_code\postman2Testcase\data\111.json')
   get_case(r'D:\code_projects\test_code\postman2Testcase\data\postman_医馆中心(开发测试)postman.json',
                            r'D:\code_projects\test_code\postman2Testcase\data\111.yaml')
