with open('src/LandingPage.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('href="#"', 'href="/#"')

with open('src/LandingPage.js', 'w', encoding='utf-8') as f:
    f.write(text)
