f = open('frontend/src/components/LandingPage.jsx', 'r', encoding='utf-8')
c = f.read()
f.close()

old = '<a href="/blog" onClick={(e)=>{e.stopPropagation();window.location.href="/blog"}}>Blog</a>'
new = '<a href="#" onClick={(e)=>{e.preventDefault();window.location.assign("/blog")}}>Blog</a>'

c = c.replace(old, new)

f = open('frontend/src/components/LandingPage.jsx', 'w', encoding='utf-8')
f.write(c)
f.close()

if 'assign("/blog")' in c:
    print('Done - fixed!')
else:
    print('FAILED - checking current state:')
    for i, line in enumerate(c.split('\n')):
        if 'Blog' in line or 'blog' in line:
            print(f'  Line {i+1}: {line.strip()}')
