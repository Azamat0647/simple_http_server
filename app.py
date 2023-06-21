from settings import TEMPLATES_PATH, STATIC_PATH
import os
from urls import urlpatterns

files_cache = {}
templ_cache = {}
responce_cache = {}

http_codes = {
    200 : 'OK',
    404 : 'NOT FOUND',
    204 : 'NO CONTENT'
}


def get_http_responce(data=b'', length=0, http_ver=1.1, code=200, data_type='html', encoding='utf-8'):
    if not (length and data) and code == 200:
        code = 204

    content_type = "image/" if data_type in ('png', 'jpeg', 'jpg') else "text/"
    content_type += data_type

    res = f'HTTP/{http_ver} {code} {http_codes.get(code, "No")}\r\n'

    if code not in (204, 304) and not (200 > code >= 100):
        res += f'Content-Type:{content_type};charset={encoding}\r\n' + \
               f'Content-Length: {length}\r\n\r\n'
        res = bytes(res, 'utf-8')
        res += data
    else:
        res += '\r\n'
        res = bytes(res, 'utf-8')

    return res

def handling_request(request):
    first_line = request.split('\r\n')[0]
    method, url_path = first_line.split(' ')[:2]

    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                             os.path.normpath(STATIC_PATH).strip('\\'), 
                             os.path.normpath(url_path).strip('\\'))

    # if method == 'POST':
    #     print(f"\n\n{request}\n\n")
    
    if os.path.isfile(file_path):
        file_type = os.path.split(file_path)[-1].split('.')[-1]
        return get_http_responce(*file_read(file_path), data_type=file_type)
    
    elif url_path in urlpatterns:
        templ_name = urlpatterns[url_path]
        return get_http_responce(*file_read(templ_name))
    
    return get_http_responce(code=404)
        



def file_read(file_name):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), TEMPLATES_PATH, file_name)

    if not os.path.exists(path):
        return '', 0
    
    length = os.path.getsize(path)
    with open(path, 'rb') as f:
        res = f.read()

    return res, length

