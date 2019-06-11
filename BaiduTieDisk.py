import requests,json,hashlib,os,sys
from pymediainfo import MediaInfo
chunk_size=524288
BDUSS=""
TBS_URL="http://tieba.baidu.com/dc/common/tbs"
FIRST_POST_URL="http://c.tieba.baidu.com/c/c/video/uploadVideoStatus"
SECOND_POST_URL="http://c.tieba.baidu.com/c/c/video/uploadVideoData"
upload_id=""
file_path=""
filesize=0
chunk_sum=0
duration=14
video_md5=""
tbs=""
session=requests.Session()

def bduss_maker():
    return "BDUSS="+BDUSS+";"

def get(url):
    return session.get(url, headers={"Cookie":bduss_maker()})


def post(url,data,files=None):
    return session.post(url,data,files=files)

def hash(str):
    m=hashlib.md5()
    str="".join(str.split("&"))
    m.update((str+"tiebaclient!!!").encode('utf-8'))
    return m.hexdigest()

def file_hash():
    with open(file_path,"rb") as file:
        global video_md5
        video_md5= hashlib.md5(file.read()).hexdigest()



def add_sign(str):
    return str+"&sign="+hash(str)

def first_post_maker():
    return "BDUSS=%s&chunk_size=%d&chunk_sum=%d&is_merge=0&tbs=%s&video_len=%d&video_md5=%s&video_size=%d" \
           % (BDUSS,chunk_size,chunk_sum,tbs,duration,video_md5,filesize)

def second_post_maker(chunk_no,chunk_size):
    return "BDUSS=%s&chunk_no=%d&chunk_size=%d&chunk_sum=%d&is_merge=0&tbs=%s&upload_id=%s&video_len=%d&video_md5=%s&video_size=%d" \
           % (BDUSS,chunk_no,chunk_size,chunk_sum,tbs,upload_id,duration,video_md5,filesize)

def second_post_dict_maker(chunk_no,chunk_size,sign):
    return {
        "BDUSS":BDUSS,
        "chunk_no": chunk_no,
        "chunk_size": chunk_size,
        "chunk_sum":chunk_sum,
        "is_merge": 0,
        "tbs": tbs,
        "upload_id": upload_id,
        "video_len":duration,
        "video_md5":video_md5,
        "video_size":filesize,
        "sign":sign
    }

def third_post_maker():
    return "BDUSS=%s&chunk_size=%d&chunk_sum=%d&is_merge=1&tbs=%s&upload_id=%s&video_len=%d&video_md5=%s&video_size=%d" %\
           (BDUSS,chunk_size,chunk_sum,tbs,upload_id,duration,video_md5,filesize)

# def second_post_second_maker(chunk_no,chunk_size,file_path,hash):
#     return {
#         "BDUSS":BDUSS,
#         "chunk_no":chunk_no,
#         "chunk_size":chunk_size,
#         "upload_id":upload_id,
#         "sign":hash,
#         "video_chunk":open(file_path,"rb")
#     }


def get_tbs():
    global tbs
    tbs= json.loads(get(TBS_URL).content.decode())["tbs"]


def video_info_getter():
    global filesize,chunk_sum,duration
    filesize=os.stat(file_path).st_size
    chunk_sum=filesize//chunk_size
    if chunk_sum*chunk_size!=filesize:
        chunk_sum+=1
    mi=MediaInfo.parse(file_path).tracks[0]
    duration=mi.duration//1000



if __name__ =="__main__":
    file=sys.argv[1]
    file_path=file
    get_tbs()

    video_info_getter()
    file_hash()
    a = post(FIRST_POST_URL,data=add_sign(first_post_maker()))
    if "video_url" in json.loads(a.content.decode())["data"]:
        print(json.loads(a.content.decode())["data"]["video_url"])
        sys.exit(0)
    upload_id=json.loads(a.content.decode())["data"]["upload_id"]

    with open(file_path,"rb") as file:
        chunk_no=1
        cc_size=chunk_size
        while True:
            video_chunk=file.read(chunk_size)
            cc_size=len(video_chunk)
            if not video_chunk:
                break
            # sdata=add_sign()
            a=post(SECOND_POST_URL,data=second_post_dict_maker(chunk_no,cc_size,hash(second_post_maker(chunk_no,cc_size))),files={"video_chunk":video_chunk})
            a.content.decode()
            print(str(chunk_no)+"/"+str(chunk_sum),end="\r")
            chunk_no+=1

    a = post(FIRST_POST_URL, data=add_sign(first_post_maker()))
    print(json.loads(a.content.decode())["data"]["video_url"])