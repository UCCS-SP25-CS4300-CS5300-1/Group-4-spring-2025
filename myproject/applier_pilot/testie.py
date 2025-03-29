class MyClass():


    x = 70

    def afun(self):

        self.x = 90 if (self.x == 70) else 0


a = MyClass()


print(a.x)
a.afun()
print(a.x)




a.afun()
print(a.x)

print("asdf")
weird = "…"
real = "..."
print("…")
print("...")

print("True" if weird == "..." else "False")
print("True" if isinstance(weird, str) else "False")
#print("True" if isinstance(int(weird), int) else "False")
print(ord(weird))



page9 = 9
page10 = 10
ellipsis = "…"

if isinstance(ellipsis, str):
    print("herro")

if ellipsis == weird:
    print("truesd")

job_list = []



for i in range(5):
    adict = {'job_title': 'job_title', 'location': 'location', 'link': '.com'}
    adict['job_title'] = 'other_job{}'.format(i)
    # adict = {'job_title': 'job_title', 'location': 'location', 'link': '.com'}
    job_list.append(adict)

for i in job_list:
    for k,v in i.items():
        print(k,v)


