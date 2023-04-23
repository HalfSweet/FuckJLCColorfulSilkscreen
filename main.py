#!/bin/python
# -*- coding: UTF-8 -*-

import argparse
import logging
import os
import secrets
import shutil
import xml.etree.ElementTree as ET

import gerber
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import base64
from PIL import Image

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(description='这是一个将图片格式转化为合法的嘉立创EDA彩色丝印的脚本')

parser.add_argument('-ti', '--topImagePath', type=str, help='顶层图片的路径')
parser.add_argument('-bi', '--bottomImagePath', type=str, help='底层图片的路径')
parser.add_argument('-o', '--out', type=str, default='./out', help='输出文件的路径')
parser.add_argument('-g', '--gerberPath', type=str, default='None', help='Gerber文件的路径，使用lceda'
                                                                         '的默认文件名，如果不是，请手动指定边框层的路径')
parser.add_argument('-kp', '--outlinePath', type=str, default='None', help='边框层的路径')
# parser.add_argument('-to', '--topSilkscreenPath', type=str, default='None', help='顶层丝印的路径')
# parser.add_argument('-bo', '--bottomSilkscreenPath', type=str, default='None', help='底层丝印的路径')

args = parser.parse_args()
SVGHeader = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'


def Image2Base64(imagePath):
    """
    将图片转换为base64编码
    :param imagePath:图片路径
    :return:base64编码
    """
    with open(imagePath, 'rb') as f:
        suffix = os.path.splitext(imagePath)[-1]
        imageBase64 = base64.b64encode(f.read()).decode('utf-8')
        return f'data:image/{suffix[1:]};base64,{imageBase64}'


def mm2mil10(mm):
    """
    把mm转换为1/10mil
    :param mm:毫米
    :return:1/10mil
    """
    return float(mm / 0.254)


def TopSVG(originX, originY, PCBWidth, PCBHeight):
    """
    生成顶层丝印的SVG
    :return:
    """
    root = ET.Element('svg', attrib={'width': f'{PCBWidth}mm', 'height': f'{PCBHeight}mm',
                                     'boardBox': f'{mm2mil10(originX)} {mm2mil10(originY)} {mm2mil10(PCBWidth)} {mm2mil10(PCBHeight)}',
                                     'viewBox': f'{mm2mil10(originX)} {mm2mil10(originY)} {mm2mil10(PCBHeight)} {mm2mil10(PCBHeight)}',
                                     'version': '1.1',
                                     'xmlns:inkscape': 'http://www.inkscape.org/namespaces/inkscape',
                                     'xmlns:sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
                                     'xmlns:xlink': 'http://www.w3.org/1999/xlink',
                                     'xmlns': 'http://www.w3.org/2000/svg',
                                     'xmlns:svg': 'http://www.w3.org/2000/svg'})

    defs0 = ET.SubElement(root, 'defs')
    defs0ClipPath = ET.SubElement(defs0, 'clipPath', attrib={'id': 'clipPath0'})
    defs0ClipPathPath = ET.SubElement(defs0ClipPath, 'path', attrib={
        'd': f'M {mm2mil10(originX) + 0.05} {mm2mil10(originY + PCBHeight) - 0.05} '
             f'L {mm2mil10(originX) + 0.05} {mm2mil10(originY) + 0.05} '
             f'{mm2mil10(originX + PCBWidth) - 0.05} {mm2mil10(originY) + 0.05} '
             f'{mm2mil10(originX + PCBWidth) - 0.05} {mm2mil10(originY + PCBHeight) - 0.05} '
             f'{mm2mil10(originX) + 0.05} {mm2mil10(originY + PCBHeight) - 0.05} ',
        'id': 'outline0',
        'stroke': 'none',
        'style': 'fill-opacity:1;fill-rule:nonzero;fill:block;'})

    defs1 = ET.SubElement(root, 'defs')
    defs1ClipPath = ET.SubElement(defs1, 'clipPath', attrib={'id': 'clipPath1',
                                                             'clip-path': 'url(#clipPath0)'})
    defs1ClipPathPath = ET.SubElement(defs1ClipPath, 'path', attrib={
        'd': f'M {mm2mil10(originX) - 0.05} {mm2mil10(originY + PCBHeight) + 0.05} '
             f'L {mm2mil10(originX) - 0.05} {mm2mil10(originY) - 0.05} '
             f'{mm2mil10(originX + PCBWidth) + 0.05} {mm2mil10(originY) - 0.05} '
             f'{mm2mil10(originX + PCBWidth) + 0.05} {mm2mil10(originY + PCBHeight) + 0.05} '
             f'{mm2mil10(originX) - 0.05} {mm2mil10(originY + PCBHeight) + 0.05} ',
        'id': 'solder1',
        'stroke': 'none',
        'style': 'fill-opacity:1;fill-rule:nonzero;fill:block;'})

    group = ET.SubElement(root, 'g', attrib={
        'clip-path': 'url(#clipPath1)',
        'transform': 'scale(1 1) translate(0 0)'
    })
    groupDefualtPath = ET.SubElement(group, 'path', attrib={
        'd': f'M {mm2mil10(originX) - 0.05} {mm2mil10(originY + PCBHeight) + 0.05} '
             f'L {mm2mil10(originX + PCBWidth) + 0.05} {mm2mil10(originY + PCBHeight) + 0.05} '
             f'{mm2mil10(originX + PCBWidth) + 0.05} {mm2mil10(originY) - 0.05} '
             f'{mm2mil10(originX) - 0.05} {mm2mil10(originY) - 0.05} '
             f'{mm2mil10(originX + PCBWidth) + 0.05} {mm2mil10(originY + PCBHeight) + 0.05} ',
        'fill': '#FFFFFF',
        'stroke': 'none',
        'stroke-width': '0',
        'id': 'background'
    })

    im = Image.open(args.topImagePath)
    imageWidth, imageHeight = im.size
    im.close()

    with open(args.topImagePath, 'rb') as f:
        base64.b64encode(f.read())

    image = ET.SubElement(group, 'image', attrib={
        'width': f'{imageWidth}',
        'height': f'{imageWidth}',
        'preserveAspectRatio': 'none',
        "xlink:href": f'{Image2Base64(args.topImagePath)}',
        'transform': f'matrix('
                     f'{mm2mil10(PCBWidth) / imageWidth} '
                     f'0 '
                     f'0 '
                     f'{mm2mil10(PCBHeight) / imageHeight} '
                     f'{mm2mil10(originX)} '
                     f'{mm2mil10(originY)})'
    })

    # 将根元素转换为字符串
    svgStr = SVGHeader + ET.tostring(root).decode('utf-8')

    with open('Top.svg', 'w') as f:
        f.write(svgStr)

    # tree = ET.ElementTree(root)
    # tree.write('Top.svg')


def BottomSVG(originX, originY, PCBWidth, PCBHeight):
    """
    生成底层丝印的SVG
    :return:
    """
    root = ET.Element('svg', attrib={'width': f'{PCBWidth}mm', 'height': f'{PCBHeight}mm',
                                     'boardBox': f'{mm2mil10(originX)} {mm2mil10(originY)} {mm2mil10(PCBWidth)} {mm2mil10(PCBHeight)}',
                                     'viewBox': f'{mm2mil10(originX)} {mm2mil10(originY)} {mm2mil10(PCBHeight)} {mm2mil10(PCBHeight)}',
                                     'version': '1.1',
                                     'xmlns:inkscape': 'http://www.inkscape.org/namespaces/inkscape',
                                     'xmlns:sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
                                     'xmlns:xlink': 'http://www.w3.org/1999/xlink',
                                     'xmlns': 'http://www.w3.org/2000/svg',
                                     'xmlns:svg': 'http://www.w3.org/2000/svg'})

    defs0 = ET.SubElement(root, 'defs')
    defs0ClipPath = ET.SubElement(defs0, 'clipPath', attrib={'id': 'clipPath0'})
    defs0ClipPathPath = ET.SubElement(defs0ClipPath, 'path', attrib={
        'd': f'M {mm2mil10(originY + PCBHeight) - 0.05} {mm2mil10(originX) + 0.05} '
             f'L {mm2mil10(originX + PCBHeight) - 0.05} {mm2mil10(originY + PCBHeight) - 0.05} '
             f'{mm2mil10(originX) + 0.05} {mm2mil10(originY + PCBHeight) - 0.05} '
             f'{mm2mil10(originX) + 0.05} {mm2mil10(originY) + 0.05} '
             f'{mm2mil10(originX + PCBWidth) - 0.05} {mm2mil10(originY) + 0.05} ',
        'id': 'outline0',
        'stroke': 'none',
        'style': 'fill-opacity:1;fill-rule:nonzero;fill:block;'})

    defs1 = ET.SubElement(root, 'defs')
    defs1ClipPath = ET.SubElement(defs1, 'clipPath', attrib={'id': 'clipPath1',
                                                             'clip-path': 'url(#clipPath0)'})
    defs1ClipPathPath = ET.SubElement(defs1ClipPath, 'path', attrib={
        'd': f'M {mm2mil10(originX) - 0.05} {mm2mil10(originY + PCBHeight) + 0.05} '
             f'L {mm2mil10(originX) - 0.05} {mm2mil10(originY) - 0.05} '
             f'{mm2mil10(originX + PCBWidth) - 0.05} {mm2mil10(originY) - 0.05} '
             f'{mm2mil10(originX + PCBWidth) - 0.05} {mm2mil10(originY + PCBHeight) - 0.05} '
             f'{mm2mil10(originX) - 0.05} {mm2mil10(originY + PCBHeight) - 0.05} ',
        'id': 'solder1',
        'stroke': 'none',
        'style': 'fill-opacity:1;fill-rule:nonzero;fill:block'})

    group = ET.SubElement(root, 'g', attrib={
        'clip-path': 'url(#clipPath1)',
        'transform': f'scale(-1 1) translate(-{mm2mil10(2 * originX + PCBWidth)} 0)'
    })

    groupDefualtPath = ET.SubElement(group, 'path', attrib={
        'd': f'M {mm2mil10(originX) - 0.05} {mm2mil10(originY + PCBHeight) + 0.05} '
             f'L {mm2mil10(originX + PCBWidth) + 0.05} {mm2mil10(originY + PCBHeight) + 0.05} '
             f'{mm2mil10(originX + PCBWidth) + 0.05} {mm2mil10(originY) - 0.05} '
             f'{mm2mil10(originX) - 0.05} {mm2mil10(originY) - 0.05} '
             f'{mm2mil10(originX) - 0.05} {mm2mil10(originY + PCBHeight) + 0.05} ',
        'fill': '#FFFFFF',
        'stroke': 'none',
        'stroke-width': '0',
        'id': 'background'
    })

    im = Image.open(args.bottomImagePath)
    imageWidth, imageHeight = im.size
    im.close()

    with open(args.bottomImagePath, 'rb') as f:
        base64.b64encode(f.read())

    image = ET.SubElement(group, 'image', attrib={
        'width': f'{imageWidth}',
        'height': f'{imageWidth}',
        'preserveAspectRatio': 'none',
        "xlink:href": f'{Image2Base64(args.bottomImagePath)}',
        'transform': f'matrix('
                     f'{-(mm2mil10(PCBWidth) / imageWidth)} '
                     f'-4.8214441229528465e-18 '
                     f'4.8214441229528465e-18 '
                     f'{(mm2mil10(PCBHeight) / imageHeight)} '
                     f'{mm2mil10(originX + PCBWidth)} '
                     f'{mm2mil10(originY)} '
        # f'{mm2mil10(originX+PCBWidth)} '
        # f'{-(mm2mil10(originY+PCBHeight))} '
                     f')',
    })

    # 将根元素转换为字符串
    svgStr = SVGHeader + ET.tostring(root).decode('utf-8')

    with open('Bottom.svg', 'w') as f:
        f.write(svgStr)


def GetBorderOrigin(path):
    """
    获取Gerber的边框层的左上角坐标
    :param path: Gerber文件的路径
    :return: 返回一个元组，分别为左上角的X坐标和Y坐标，然后是PCB的宽度和高度，单位为mm
    """
    # 读取Gerber文件
    border_layer = gerber.read(path)

    # 获取边框层的边界
    bounds = border_layer.bounds

    # 获取左上角的坐标
    originX = bounds[0][0]
    originY = -bounds[1][1]  # 对坐标的Y轴进行了翻转，SVG中Y轴向下为正方向

    width = bounds[0][1] - bounds[0][0]
    hight = bounds[1][1] - bounds[1][0]

    logging.info(f'您的PCB宽度为: {width}mm，高度为: {hight}mm')
    logging.info(f'您的PCB左上角坐标为: ({originX}, {originY})')
    return originX, originY, width, hight


def EncryptFile():
    # svg_file = './fix.svg'

    aes_key = secrets.token_bytes(16)
    aes_iv = secrets.token_bytes(16)

    pub_key = '''-----BEGIN PUBLIC KEY-----
        MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzPtuUqJecaR/wWtctGT8
        QuVslmDH3Ut3s8c1Ls4A+M9rwpeLjgDUqfcrSrTHBrl5k/dOeJEWMeNF7STWS5jo
        WZE0H60cvf2bhormC9S6CRwq4Lw0ua0YQMo66R/qCtLVa5w6WkaPCz4b0xaHWtej
        JH49C0T67rU2DkepXuMPpwNCflMU+WgEQioZEldUTD6gYpu2U5GrW4AE0AQiIo+j
        e7tgN8PlBMbMaEfu0LokZyth1ugfuLAgyogWnedAegQmPZzAUe36Sni94AsDlhxm
        mjFl+WQZzD3MclbEY6KQB5XL8zCR/J6pCUUwfHantLxY/gQi0XJG5hWWtDyH/fR2
        lwIDAQAB
        -----END PUBLIC KEY-----
        '''

    rsa_key = RSA.importKey(pub_key)
    cipher_rsa = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA256)
    enc_aes_key = cipher_rsa.encrypt(aes_key)
    enc_aes_iv = cipher_rsa.encrypt(aes_iv)

    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=aes_iv)
    with open('Top.svg', 'rb') as f:
        svgData = f.read()
        enc_svg_data = cipher_aes.encrypt(svgData)
        tag = cipher_aes.digest()

    with open(args.out + '/Fabrication_ColorfulTopSilkscreen.FCTS', 'wb') as f:
        f.write(enc_aes_key)
        f.write(enc_aes_iv)
        f.write(enc_svg_data)
        f.write(tag)

    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=aes_iv)
    with open('Bottom.svg', 'rb') as f:
        svgData = f.read()
        enc_svg_data = cipher_aes.encrypt(svgData)
        tag = cipher_aes.digest()

    with open(args.out + '/Fabrication_ColorfulBottomSilkscreen.FCBS', 'wb') as f:
        f.write(enc_aes_key)
        f.write(enc_aes_iv)
        f.write(enc_svg_data)
        f.write(tag)


def CopyFile():
    shutil.copytree(args.gerberPath, "./out")
    pass


if __name__ == '__main__':
    if args.gerberPath == 'None':
        if args.outlinePath == 'None':
            logging.error('请指定lceda风格的Gerber文件的路径或者边框层文件的路径')
            exit(1)

    if args.gerberPath == 'None':
        outlinePath = args.outlinePath
    else:
        outlinePath = args.gerberPath + "/Gerber_BoardOutlineLayer.GKO"
        CopyFile()

    originX, originY, PCBWidth, PCBHeight = GetBorderOrigin(outlinePath)

    TopSVG(originX, originY, PCBWidth, PCBHeight)
    BottomSVG(originX, originY, PCBWidth, PCBHeight)
    EncryptFile()

