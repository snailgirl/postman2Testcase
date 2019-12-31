from flask import Flask, render_template, request, send_from_directory,session,make_response
from main import *
import os
import time
import urllib.request

upload_path = os.path.join(os.path.dirname(__file__), 'data')  # 文件上传下载路径
app = Flask(__name__)
app.secret_key = 'xmindhellodfdf'

@app.route('/index',methods=['GET','POST'])
def index():
    session['tag'] = False
    if request.method == 'POST':
        res = {
            'error': '',
            'file_url_json': '',
            'sucess_msg': '',
            'sucess_msg_json': '',
            'file_url_yaml': '',
            'sucess_msg_yaml': ''
        }

        def del_files():
            '''
            删除upload下所有的文件(除__init__.py)
            :return:
            '''
            for file_name in os.listdir(upload_path):
                del_files_path = os.path.join(upload_path, file_name)
                if file_name not in ['__init__.py']:
                    # 获取文件的创建日期
                    ctime = time.localtime(os.stat(del_files_path).st_ctime)
                    cdate = time.strftime("%Y-%m-%d", ctime)
                    # 获取文件创建日期小于当前日期
                    if cdate < time.strftime("%Y-%m-%d"):
                        os.remove(del_files_path)
        # 删除upload下所有的文件(除__init__.py)
        del_files()

        # 获取上传的postman json文件
        postman_file_obj = request.files['jsonFile']
        postman_file_name = postman_file_obj.filename
        # 判断json文件后缀是否正确
        if not postman_file_name.endswith('.json'):
            res['error'] = '上传的postman json 文件不正确！'
            return render_template('index.html', res = res)
        # 保存上传的文件
        postman_testset_file = os.path.join(upload_path, 'postman_' + postman_file_name)
        postman_file_obj.save(postman_testset_file)

        def output_file(postman_testset_file, postman_file_name, res):
            '''
            生成httprunner 测试用例(json/yaml)
            :param postman_testset_file: 上传的postman json 文件路径
            :param postman_file_name: 上传的postman json文件的文件名
            :param res:
            :return:
            '''
            res['sucess_msg'] = postman_file_name + ' 用例转换成功！'
            # 生成用例的文件路径
            output_json_file_name = os.path.join(upload_path, postman_file_name.rsplit('.', 1)[0] + '.json')
            output_yaml_file_name = os.path.join(upload_path, postman_file_name.rsplit('.', 1)[0] + '.yaml')
            # 生成json文件路径
            get_case(postman_testset_file, output_json_file_name)
            res['file_url_json'] = os.path.join('/download/', postman_file_name.rsplit('.', 1)[0] + '.json')
            res['sucess_msg_json'] = '点击下载！'
            # 生成yaml文件路径
            get_case(postman_testset_file, output_yaml_file_name)
            res['file_url_yaml'] = os.path.join('/download/', postman_file_name.rsplit('.', 1)[0] + '.yaml')
            res['sucess_msg_yaml'] = '点击下载！'
            return res
        # 生成httprunner测试用例，返回res
        res = output_file(postman_testset_file, postman_file_name, res)
        return render_template('index.html', res = res)
    return render_template('index.html', res = {})

@app.route('/download/<filename>',methods=['GET'])
def download(filename):
    file_name = urllib.request.unquote(filename, encoding='utf-8', errors='replace')
    # 下载的文件路径
    excel_file_path = os.path.join(upload_path, file_name)
    if request.method == "GET":
        if os.path.isfile(excel_file_path):
            return send_from_directory(upload_path, file_name, as_attachment=True)

if __name__ == '__main__':
    app.run()
