f = open('frontend/src/components/LandingPage.jsx', 'r', encoding='utf-8')
c = f.read()
f.close()

old = '<a href="/blog">Blog</a>'
new = '<a href="/blog" onClick={(e)=>{e.stopPropagation();window.location.href="/blog"}}>Blog</a>'

c = c.replace(old, new)

f = open('frontend/src/components/LandingPage.jsx', 'w', encoding='utf-8')
f.write(c)
f.close()

print('Done' if 'stopPropagation' in c else 'FAILED - pattern not found')
