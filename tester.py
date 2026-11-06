import json

def readdict(filename):
    with open(filename, "r") as file:
        my_dict = json.load(file)
    return my_dict

def writedict(filename, my_dict):
    with open(filename, "w") as file:
        json.dump(my_dict, file, indent=4)

myini = {"downloadpath":"c:/olade/config.ini",
         "videoformat": "MKV",
         "Logo": "mylogo.com",
         "Splashtime": 300
         }  

fn = "E:\\configx.txt"
writedict(fn, myini)  

odict = readdict(fn)
#print(odict)

for key, value in odict.items():
    print(f"{key} = {value}")