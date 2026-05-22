with open("vip_signal_scanner.py","r") as f: s=f.read()
print("ANY bug:", s.count("ANY(:vn30_list)"), "(phai = 0)")
print("t bug:", s.count("'{t}'"), "(phai = 0)")
print("HPG in SQL:", "'HPG'" in s)
