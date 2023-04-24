import cv2
from Crypto.Cipher import AES
import base64
from PIL import Image, ImageDraw, ImageFont

import base64
import numpy as np
def encrypt(s, key):
    def pad(m):
        left = 16 - len(m) % 16
        return m + chr(left) * left

    cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
    enc_byte = cipher.encrypt(pad(s).encode("utf-8"))
    return base64.b64encode(enc_byte).decode("ascii")

def getImageFromBase64(b64):
    buffer = base64.b64decode(b64)
    nparr = np.frombuffer(buffer, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image

def decrypt(s, key):
    cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
    b = cipher.decrypt(base64.b64decode(s))
    return b[: -b[-1]]

def findContour(img):
    if cv2.__version__.startswith('3'):
        _, contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    else: 
        contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def find_if_close(cnt1, cnt2):
        row1, row2 = cnt1.shape[0], cnt2.shape[0]
        for i in range(row1):
            for j in range(row2):
                dist = np.linalg.norm(cnt1[i] - cnt2[j])
                if abs(dist) < 2:
                    return True
                elif i == row1 - 1 and j == row2 - 1:
                    return False

    LENGTH = len(contours)
    status = np.zeros((LENGTH, 1))
    for i, cnt1 in enumerate(contours):
        x = i
        if i != LENGTH - 1:
            for j, cnt2 in enumerate(contours[i + 1 :]):
                x = x + 1
                dist = find_if_close(cnt1, cnt2)
                if dist == True:
                    val = min(status[i], status[x])
                    status[x] = status[i] = val
                else:
                    if status[x] == status[i]:
                        status[x] = i + 1
    unified = []
    maximum = int(status.max()) + 1
    for i in range(maximum):
        pos = np.where(status == i)[0]
        if pos.size != 0:
            cont = np.vstack([contours[i] for i in pos])
            hull = cv2.convexHull(cont)
            unified.append(hull)
    return unified

def extractChar(img, contour):
    mult = 1.1
    ret = []
    pt = []
    for cnt in contour:
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        W = rect[1][0]
        H = rect[1][1]
        if W * H < 10:
            continue

        Xs = [i[0] for i in box]
        Ys = [i[1] for i in box]
        x1 = min(Xs)
        x2 = max(Xs)
        y1 = min(Ys)
        y2 = max(Ys)

        rotated = False
        angle = rect[2]

        if angle < -45:
            angle += 90
            rotated = True

        center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
        size = (int(mult * (x2 - x1)), int(mult * (y2 - y1)))

        M = cv2.getRotationMatrix2D((size[0] / 2, size[1] / 2), angle, 1.0)

        cropped = cv2.getRectSubPix(img, size, center)
        cropped = cv2.warpAffine(cropped, M, size)

        croppedW = W if not rotated else H
        croppedH = H if not rotated else W

        croppedRotated = cv2.getRectSubPix(
            cropped,
            (int(croppedW * mult), int(croppedH * mult)),
            (size[0] / 2, size[1] / 2),
        )

        if croppedRotated.size < 200:
            continue
        if np.mean(croppedRotated) < 30:
            continue
        im = cv2.resize(croppedRotated, (30, 30))
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32)
        im = cv2.filter2D(im, -1, kernel=kernel)
        ret.append(im)
        pt.append((rect[0][0], rect[0][1]))
    return ret, pt


def genCharacter(ch, size):
    img = Image.new("L", size, 0)
    font = ImageFont.truetype("simsun.ttc", min(size))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), ch, font=font, fill=255)
    return np.asarray(img)

def crack(data):
    img = getImageFromBase64(data["originalImageBase64"])
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, img = cv2.threshold(img, 1, 255, cv2.THRESH_BINARY)
    img = cv2.bilateralFilter(img, 5, 200, 200)
    img = cv2.bitwise_not(img)
    cnt = findContour(img)
    ch, pt = extractChar(img, cnt)
    wd = [genCharacter(w, (30, 30)) for w in data["wordList"]]
    score = []
    for i, w in enumerate(wd):
        for j, c in enumerate(ch):
            score.append(((i, j), cv2.bitwise_xor(c, w).sum()))
    score.sort(key=lambda x: x[1])
    wset = set()
    cset = set()
    ans = {}

    for s in score:
        if s[0][0] in wset or s[0][1] in cset:
            continue
        wset.add(s[0][0])
        cset.add(s[0][1])
        ans[data["wordList"][s[0][0]]] = pt[s[0][1]]

    return [{"x": int(ans[w][0]), "y": int(ans[w][1])} for w in data["wordList"]]
