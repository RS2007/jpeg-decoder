#!/bin/python3.8
import numpy as np


def genY(r, g, b):
    y = 16 + (((r << 6) + (r << 1) + (g << 7) + g + (b << 4) + (b << 3) + b) >> 8)
    # (can vectorize look into later)
    # y = ((0.257*r + 0.504*g + (0.098)*b)) + 16
    return y


def genCb(r, g, b):
    cb = 128 + (
        (
            -((r << 5) + (r << 2) + (r << 1))
            - ((g << 6) + (g << 3) + (g << 1))
            + (b << 7)
            - (b << 4)
        )
        >> 8
    )
    # (can vectorize look into later)
    # cb = 128 + ((-0.148)*r - (0.291*g) + (0.439*b))
    return cb


def genCr(r, g, b):
    cr = 128 + (
        ((r << 7) - (r << 4) - ((g << 6) + (g << 5) - (g << 1)) - ((b << 4) + (b << 1)))
        >> 8
    )
    # (can vectorize look into later)
    # cr = 128 + ((0.439*r) - (0.368*g) - (0.071*b))
    return cr


def rgbToycbcr(rgbImg):
    height, width, _ = rgbImg.shape
    arr = np.zeros((height, width, 3))
    for i in range(height):
        for j in range(width):
            b, g, r = rgbImg[i][j]
            arr[i][j] = [
                genY(r, g, b),
                genCr(r, g, b),
                genCb(r, g, b),
            ]
    return arr


class APP:
    def __init__(self):
        self.payloadLength = 0
        self.type = 0
        self.mainVersion = 0
        self.subVersion = 0
        self.pixelUnitDensity = 0
        self.horizontalPixelDensity = 0
        self.verticalPixelDensity = 0
        self.horizontalPixelCountThumb = 0
        self.verticalPixelCountThumb = 0


class DQT:
    def __init__(self):
        self.segmentLength = 0
        self.precisonAndTable = 0
        self.quantTaleData = 0


class SOF:
    def __init__(self):
        self.segmentLength = 0
        self.precision = 0
        self.imageHeight = 0
        self.imageWidth = 0
        self.numOfComponents = 0
        self.byteData = 0


class DHT:
    def __init__(self):
        self.dhtData = 0
        self.segmentLength = 0
        self.huffmanTableInfo = 0
        self.symbolCount = 0


class SOS:
    def __init__(self):
        self.segmentLength = 0
        self.componentCount = 0
        self.componentData = 0


PROPERTIES_APP_BIT_LENGTH = [
    {"payloadLength": 2},
    {"type": 4},
    {"null": 1},
    {"mainVersion": 1},
    {"subVersion": 1},
    {"pixelUnitDensity": 1},
    {"horizontalPixelDensity": 2},
    {"verticalPixelDensity": 2},
    {"horizontalPixelCountThumb": 1},
    {"verticalPixelCountThumb": 1},
]

PROPERTIES_DQT_BIT_LENGTH = [
    {"segmentLength": 2},
    {"precisonAndTable": 1},
    {"quantTaleData": 64},
]

PROPERTIES_SOF_BIT_LENGTH = [
    {"segmentLength": 2},
    {"precision": 1},
    {"imageHeight": 2},
    {"imageWidth": 2},
    {"numOfComponents": 1},
    {"byteData": 9},
]

PROPERTIES_DHT_BIT_LENGTH = [
    {"segmentLength": 2},
    {"huffmanTableInfo": 1},
    {"symbolCount": 16},
    {"dhtData": 10},
]

PROPERTIES_SOS_BIT_LENGTH = [
    {"segmentLength": 2},
    {"componentCount": 1},
    {"componentData": 2},
    {"skipBytes": 3},
]


def parseAPP(f):
    app = APP()
    for x in PROPERTIES_APP_BIT_LENGTH:
        key, value = list(x.items())[0]
        if key == "null":
            f.read(1)
            continue
        if value == 4:
            setattr(app, key, str(f.read(4)))
        else:
            setattr(app, key, str(int.from_bytes(f.read(value), "big")))
    return app


def parseDQT(f):
    dqt = DQT()
    for x in PROPERTIES_DQT_BIT_LENGTH:
        key, value = list(x.items())[0]
        if value == 64:
            st = ""
            for _ in range(32):
                st += hex(int.from_bytes(f.read(2), "big")) + " "
            setattr(dqt, key, st)
        else:
            setattr(dqt, key, str(int.from_bytes(f.read(value), "big")))
    return dqt


def parseSOF(f):
    sof = SOF()
    for x in PROPERTIES_SOF_BIT_LENGTH:
        key, value = list(x.items())[0]
        if value == 9:
            st = ""
            for _ in range(9):
                st += hex(int.from_bytes(f.read(1), "big")) + " "
            setattr(sof, key, st)
        else:
            setattr(sof, key, str(int.from_bytes(f.read(value), "big")))
    return sof


def parseDHT(f):
    dht = DHT()
    for x in PROPERTIES_DHT_BIT_LENGTH:
        key, value = list(x.items())[0]
        if key == "dhtData":
            value = int(dht.segmentLength) - 19
        if value == 16 or key == "dhtData":
            st = ""
            for _ in range(value):
                st += hex(int.from_bytes(f.read(1), "big")) + " "
            setattr(dht, key, st)
        else:
            setattr(dht, key, str(int.from_bytes(f.read(value), "big")))
    return dht


def parseSOS(f):
    sos = SOS()
    imageData = []
    for x in PROPERTIES_SOS_BIT_LENGTH:
        key, value = list(x.items())[0]
        if key == "skipBytes":
            for _ in range(value):
                f.read(1)
        elif key == "componentData":
            value = 2 * int(sos.componentCount)
            st = ""
            for _ in range(value):
                st += hex(int.from_bytes(f.read(1), "big")) + " "
            setattr(sos, key, st)
        else:
            setattr(sos, key, str(int.from_bytes(f.read(value), "big")))
    while (data := int.from_bytes(f.read(2), "big")) != 0xFFD9:
        imageData.append(hex(data))
    return sos, imageData


MARKERS = [
    {0xFFC0: {"class": SOF, "parser": parseSOF, "end": False, "name": "SOF"}},
    {0xFFC4: {"class": DHT, "parser": parseDHT, "end": False, "name": "DHT"}},
    {
        0xFFDA: {
            "class": SOS,
            "parser": parseSOS,
            "end": False,
            "imageDataNext": True,
            "name": "SOS",
        }
    },
    {0xFFD9: {"end": True}},
    {0xFFDB: {"class": DQT, "parser": parseDQT, "end": False, "name": "DQT"}},
    {0xFFE0: {"class": APP, "parser": parseAPP, "end": False, "name": "APP"}},
]


def binary_search_markers(type):
    s = 0
    e = len(MARKERS) - 1
    while s <= e:
        m = s + (e - s) // 2
        key, value = list(MARKERS[m].items())[0]
        if key == type:
            return value
        elif key > type:
            e = m - 1
        else:
            s = m + 1
    return -1


if __name__ == "__main__":
    finalImage = {}
    for x in MARKERS:
        key, value = list(x.items())[0]
        if "name" in value:
            finalImage[value["name"]] = []
    with open("./sample1.jfif", mode="rb") as f:
        data = f.read(2)
        if (
            int.from_bytes(data, "big") != 0xFFD8
            and int.from_bytes(f.read(2), "big") != 0xFFE0
        ):
            print("ERROR: Not a jpeg:jfif file")
        while data := int.from_bytes(f.read(2), "big"):
            val = binary_search_markers(data)
            print(hex(data), val)
            if val == -1 or val["end"]:
                break
            if val != -1:
                cl = val["parser"]
                print(cl)
                a = ""
                if "imageDataNext" in val:
                    a, image = cl(f)
                    finalImage[val["name"]].append(a.__dict__)
                    finalImage["imageData"] = image
                else:
                    a = cl(f)
                    finalImage[val["name"]].append(a.__dict__)
            else:
                print(hex(data))
    print(finalImage)
