import lxml
from lxml import etree, html
import urllib.request
import json

url = "https://docs.google.com/forms/d/e/1FAIpQLSdY53W49HhpwZ3g6H_w4GxrnPbVZt-xPvoen-KkhTHp4l72bg/"
url = "https://docs.google.com/forms/d/e/1FAIpQLSfzlSloyv4w8SmLNR4XSSnSlKJ7WFa0wPMvEJO-5cK-Zb6ZdQ/"
a = urllib.request.Request(url + "viewform")
a.add_header("User-Agent", "ABCD")

res = urllib.request.urlopen(a).read()

HTMLParser = html.HTMLParser()

etree_obj = etree.fromstring(res, HTMLParser)

LOAD_DATA = etree_obj.xpath('//*[contains(text(), "FB_PUBLIC_LOAD_DATA_")]')[0].text

[greeting, questions] = json.loads(LOAD_DATA.split(" = ", 1)[-1][:-1])[1][0:2]

# questions = json.loads(LOAD_DATA.split(' = ', 1)[-1][:-1])
try:
    image = (
        etree_obj.xpath(
            '//*[@class="freebirdFormviewerViewItemsEmbeddedobjectImageWrapper"]'
        )[0]
        .getchildren()[0]
        .attrib.get("src")
    )
except IndexError:
    image = ""

for question in questions:
    if question and len(question) == 7:
        print("!", question[1])
        print("->", image)
    elif question and len(question) == 5:

        [qid, prompt, description, type_, answers] = question
        question_ = dict(
            question_id=answers[0][0],
            prompt=prompt,
            description=description,
            answers=(
                [answer[0] for answer in answers[0][1]]
                if len(answers) and answers[0][1]
                else None
            ),
        )
        print(
            f"entry.{question_['question_id']}",
            end="\N{Soon with Rightwards Arrow Above}",
        )
        choices = (
            "("
            + (", ".join(question_["answers"]) if question_["answers"] else "")
            + ")"
        )
        if "Payment" not in prompt:
            print("?", prompt)
        else:
            print("$", prompt.split()[0], "MOB")
        if description:
            print(" -", description)
        if question_["answers"]:
            print("  -", choices)
    else:
        print(question)

print(f"{url}formResponse\N{Soon with Rightwards Arrow Above}? confirm")
