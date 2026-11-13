#!/usr/bin/env python3
"""中文：用真实玻璃绘制器生成本地设计预览；不改变固件。/ English: Local design previews using the real glass renderer; no firmware changes.

Run: python3 tools/render_glass_previews.py
Requires Pillow and a C compiler. PNGs go to ignored docs/local/glass-previews/.
The layouts are concepts, not device captures or measurements of optical output.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 684, 1216

HOST = r'''
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "ui/ui_image_dither.h"
#define DPREADER_BOARD_METALIO47 1
#define UI_LOCK_WIDTH 684
#define UI_LOCK_HEIGHT 1216
#define MALLOC_CAP_SPIRAM 1
#define MALLOC_CAP_8BIT 2
typedef struct {int x,y,width,height;} EpdRect;
static uint8_t ui_read_pixel(const uint8_t *fb,int x,int y) {
 return (fb[(y*684+x)/2] >> (4*(x&1)))&15;
}
static void epd_draw_pixel(int x,int y,uint8_t g,uint8_t *fb) {
 size_t at=(y*684+x)/2;unsigned shift=4*(x&1);
 fb[at]=(fb[at]&~(15u<<shift))|((g>>4)<<shift);
}
static void *heap_caps_malloc(size_t n,unsigned caps) {(void)caps;return malloc(n);}
static void heap_caps_free(void *p) {free(p);}
'''
MAIN = r'''
int main(int argc,char **argv) {
 if(argc!=8)return 2;
 uint8_t fb[684*1216/2];memset(fb,255,sizeof(fb));
 for(int y=0;y<1216;y++)for(int x=0;x<684;x++) {
  int v=getchar();if(v==EOF)return 3;epd_draw_pixel(x,y,(uint8_t)v,fb);
 }
 EpdRect r={atoi(argv[1]),atoi(argv[2]),atoi(argv[3]),atoi(argv[4])};
 if(!ui_glass_panel_frost(fb,r,atoi(argv[5]),atoi(argv[6]),atoi(argv[7]),true))return 4;
 for(int y=0;y<1216;y++)for(int x=0;x<684;x++)putchar(ui_read_pixel(fb,x,y)*17);
 return ferror(stdout)?5:0;
}
'''


def font(size, serif=False):
    return ImageFont.truetype(str(ROOT / 'main/assets' / ('Bitter-Regular.ttf' if serif else 'builtin.ttf')), size)


def text(img, xy, value, size=24, gray=0, anchor=None, serif=False):
    ImageDraw.Draw(img).text(xy, value, font=font(size, serif), fill=gray, anchor=anchor)


def icons():
    source = (ROOT / 'boards/metalio47/src/main/assets/ui_icons.h').read_text()
    source = re.sub(r'//[^\n]*|/\*.*?\*/', '', source, flags=re.S)
    enum = re.search(r'typedef enum\s*\{(.*?)\}', source, re.S).group(1)
    names = [n.strip() for n in enum.split(',') if n.strip() and n.strip() != 'UI_ICON_COUNT']
    data = source.split('static const uint8_t ui_icon_masks', 1)[1]
    blocks = re.findall(r'\{\s*((?:0x[0-9a-fA-F]+\s*,?\s*)+)\}', data)
    result = {}
    for name, block in zip(names, blocks):
        values = [int(v, 16) for v in re.findall(r'0x[0-9a-fA-F]+', block)]
        pixels = bytes(g for v in values for g in ((v >> 4)*17, (v & 15)*17))
        result[name.removeprefix('UI_ICON_')] = Image.frombytes('L', (72, 72), pixels)
    return result


ICONS = icons()


def icon(img, name, x, y, size=34, gray=0):
    mask = ICONS[name].resize((size, size), Image.Resampling.LANCZOS)
    img.paste(gray, (x-size//2, y-size//2, x-size//2+size, y-size//2+size), mask)


def base(reader=False):
    img = Image.new('L', (W, H), 255)
    d = ImageDraw.Draw(img)
    text(img, (30, 20), 'dpReader', 20)
    text(img, (342, 20), '09:41', 20, anchor='mt')
    icon(img, 'WIFI', 555, 32, 24)
    d.rounded_rectangle((591, 23, 627, 41), 4, outline=34, width=2)
    d.rectangle((595, 27, 619, 37), fill=34)
    text(img, (640, 20), '88', 18)
    if reader:
        text(img, (342, 76), 'TRUYỆN KIỀU', 20, 85, 'mt')
        lines = ['Trăm năm trong cõi người ta,', 'Chữ tài chữ mệnh khéo là ghét nhau.',
                 'Trải qua một cuộc bể dâu,', 'Những điều trông thấy mà đau đớn lòng.',
                 'Lạ gì bỉ sắc tư phong,', 'Trời xanh quen thói má hồng đánh ghen.',
                 'Cảo thơm lần giở trước đèn,', 'Phong tình cổ lục còn truyền sử xanh.',
                 'Rằng: Năm Gia Tĩnh triều Minh,', 'Bốn phương phẳng lặng, hai kinh vững vàng.',
                 'Có nhà viên ngoại họ Vương,', 'Gia tư nghĩ cũng thường thường bậc trung.',
                 'Một trai con thứ rốt lòng,', 'Vương Quan là chữ, nối dòng nho gia.',
                 'Đầu lòng hai ả tố nga,', 'Thúy Kiều là chị, em là Thúy Vân.']
        for i, line in enumerate(lines):
            text(img, (40+(20 if i % 2 else 0), 140+i*59), line, 26, serif=True)
        text(img, (30, 1178), 'Chương 1 · Gặp gỡ Kim Trọng', 19, 68)
        text(img, (654, 1178), '42 / 168', 19, 68, 'rt')
        return img
    text(img, (32, 90), 'Một chút bình yên.', 40)
    text(img, (34, 148), 'Thứ Năm, 12 tháng 11', 23, 102)
    d.rounded_rectangle((28, 207, 656, 571), 28, fill=238)
    # 中文：几何封面用于观察玻璃透过率。/ English: Geometric cover reveals glass transmission.
    d.rounded_rectangle((48, 226, 251, 550), 10, fill=51)
    d.ellipse((74, 251, 225, 402), fill=187)
    d.polygon([(48, 495), (150, 345), (251, 495)], fill=102)
    text(img, (149, 446), 'TRUYỆN', 25, 255, 'mt')
    text(img, (149, 480), 'KIỀU', 35, 255, 'mt')
    text(img, (279, 292), 'ĐANG ĐỌC', 18, 102)
    text(img, (278, 338), 'Truyện Kiều', 35)
    text(img, (280, 391), 'Nguyễn Du', 24, 85)
    d.rounded_rectangle((280, 452, 620, 459), 3, fill=204)
    d.rounded_rectangle((280, 452, 423, 459), 3, fill=34)
    text(img, (280, 482), '42% · Tiếp tục đọc', 22)
    text(img, (32, 625), 'Nhịp đọc của bạn', 30)
    for x, a, b in [(36, '28', 'phút hôm nay'), (255, '7', 'ngày liên tiếp'), (474, '12', 'cuốn đã đọc')]:
        text(img, (x, 689), a, 52)
        text(img, (x, 762), b, 20, 102)
    d.line((32, 826, 652, 826), fill=221)
    text(img, (32, 866), '“Chữ tâm kia mới bằng ba chữ tài.”', 25, 68, serif=True)
    text(img, (652, 921), '— Nguyễn Du', 21, 102, 'rt')
    for i, (name, label) in enumerate([('HOUSE', 'Trang chủ'), ('LIBRARY_BIG', 'Kệ sách'), ('FOLDER_OPEN', 'Tệp tin'), ('SLIDERS_HORIZONTAL', 'Cài đặt')]):
        x = 85+i*171
        icon(img, name, x, 1129, 32, 0 if i == 0 else 102)
        text(img, (x, 1160), label, 20, 0 if i == 0 else 102, 'mt')
    d.rounded_rectangle((65, 1200, 105, 1204), 2, fill=0)
    return img


def glass(exe, img, rect, white, refract, radius=32):
    raw = subprocess.run([str(exe), *map(str, (*rect, radius, white, refract))], input=img.tobytes(), capture_output=True, check=True).stdout
    return Image.frombytes('L', (W, H), raw)


def floating_navigation(exe, active=0, page=None):
    img = base() if page is None else page.copy()
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1088, W-1, H-1), fill=255)
    d.rounded_rectangle((12, 1107, 671, 1202), 48, fill=136)
    d.rounded_rectangle((12, 1104, 671, 1199), 48, fill=204)
    d.rounded_rectangle((13, 1105, 670, 1198), 47, outline=255)
    # 中文：用户参考图中的一体悬浮胶囊及独立选中底。/ English: Shared floating capsule and selected pill from the user's reference.
    for i, (name, label) in enumerate([('HOUSE', 'Trang chủ'), ('LIBRARY_BIG', 'Kệ sách'), ('FOLDER_OPEN', 'Tệp tin'), ('SLIDERS_HORIZONTAL', 'Cài đặt')]):
        x = (2*i+1)*W//8
        if i == active:
            d.rounded_rectangle((x-70, 1112, x+69, 1191), 40, fill=153)
            d.rounded_rectangle((x-69, 1113, x+68, 1190), 39, outline=255)
        icon(img, name, x, 1141, 44)
        text(img, (x, 1170), label, 17, anchor='mt')
    return quantize(img)


def settings_page(detail=False):
    img = base()
    d = ImageDraw.Draw(img)
    d.rectangle((0, 70, W-1, 1087), fill=255)
    if detail:
        icon(img, 'CHEVRON_LEFT', 50, 108, 30)
        text(img, (83, 82), 'Hiển thị', 42)
        text(img, (34, 178), 'PHÔNG CHỮ & TRANG ĐỌC', 18, 102)
        rows = [('TYPE', 'Phông chữ hệ thống', 'Mặc định'),
                ('A_LARGE_SMALL', 'Cỡ chữ giao diện', '100%'),
                ('REFRESH_CW', 'Làm mới trang chủ', 'Thông thường'),
                ('LIGHTBULB', 'Đèn nền', 'Bật · 60%'),
                ('SUN', 'Ánh sáng ấm', '35%'),
                ('CLOCK', 'Nguồn & Ngủ', 'Tự khóa sau 5 phút')]
        for i, (name, label, value) in enumerate(rows):
            y = 242+i*125
            icon(img, name, 56, y+22, 30)
            text(img, (92, y), label, 26)
            text(img, (92, y+45), value, 21, 102)
            icon(img, 'CHEVRON_RIGHT', 631, y+32, 23, 102)
            if i<5:
                d.line((92, y+104, 650, y+104), fill=221)
        return img
    text(img, (34, 82), 'Cài đặt', 46)
    d.rounded_rectangle((30, 172, 654, 303), 24, fill=255, outline=221)
    d.ellipse((52, 196, 134, 278), fill=238)
    text(img, (93, 213), 'D', 34, 68, 'mt')
    text(img, (156, 195), 'dephia31', 29)
    text(img, (156, 241), 'Hồ sơ của bạn', 21, 102)
    icon(img, 'CHEVRON_RIGHT', 623, 237, 24, 85)
    rows = [('WIFI', 'Kết nối', 'Wi-Fi · Bluetooth · KOSync · OPDS'),
            ('SUN', 'Hiển thị', 'Phông chữ · Làm mới · Nguồn & Ngủ'),
            ('SLIDERS_HORIZONTAL', 'Cá nhân hóa', 'Tủ sách · Màn hình khóa · Chữ ký'),
            ('ZAP', 'Điều khiển', 'Phím cứng & Cử chỉ'),
            ('DOWNLOAD', 'Cập nhật & Khôi phục', 'Cập nhật · Sao lưu · Chẩn đoán')]
    for i, (name, label, caption) in enumerate(rows):
        y = 351+i*132
        icon(img, name, 57, y+30, 30)
        text(img, (95, y), label, 28)
        text(img, (95, y+47), caption, 20, 102)
        icon(img, 'CHEVRON_RIGHT', 630, y+30, 22, 102)
        if i<4:
            d.line((95, y+105, 650, y+105), fill=221)
    return img


def library_page():
    img = base()
    d = ImageDraw.Draw(img)
    d.rectangle((0, 70, W-1, 1087), fill=255)
    text(img, (34, 82), 'Tủ sách', 46)
    icon(img, 'SEARCH', 570, 111, 30)
    icon(img, 'FOLDER_OPEN', 630, 111, 30)
    text(img, (34, 161), 'Tất cả sách', 22)
    text(img, (650, 161), '6 cuốn · Gần đây', 20, 102, 'rt')
    books = [('TRUYỆN', 'KIỀU', 'Truyện Kiều', 'Nguyễn Du', '42%'),
             ('SỐ', 'ĐỎ', 'Số Đỏ', 'Vũ Trọng Phụng', '18%'),
             ('TẮT', 'ĐÈN', 'Tắt Đèn', 'Ngô Tất Tố', 'Mới'),
             ('DẾ MÈN', 'PHIÊU LƯU KÝ', 'Dế Mèn', 'Tô Hoài', '85%'),
             ('VỢ', 'NHẶT', 'Vợ Nhặt', 'Kim Lân', 'Đã đọc'),
             ('CHÍ', 'PHÈO', 'Chí Phèo', 'Nam Cao', 'Mới')]
    for i, (a, b, title, author, progress) in enumerate(books):
        x = 34+(i%3)*218
        y = 226+(i//3)*373
        ink = [51, 221, 102, 238, 68, 187][i]
        contrast = 255 if ink<140 else 17
        d.rounded_rectangle((x+3, y+4, x+181, y+242), 8, fill=221)
        d.rounded_rectangle((x, y, x+178, y+238), 8, fill=ink)
        d.line((x+10, y+10, x+10, y+228), fill=153, width=2)
        if i%3==0:
            d.ellipse((x+30, y+26, x+151, y+147), outline=153, width=2)
            d.polygon([(x+17, y+172), (x+91, y+77), (x+166, y+172)], fill=119)
        elif i%3==1:
            for k in range(5):
                d.line((x+20, y+28+k*16, x+158, y+28+k*16), fill=153, width=2)
        else:
            d.rectangle((x+25, y+24, x+153, y+211), outline=contrast, width=2)
        text(img, (x+89, y+126), a, 25, contrast, 'mt')
        text(img, (x+89, y+166), b, 18 if len(b)>8 else 29, contrast, 'mt')
        text(img, (x, y+254), title, 25)
        text(img, (x, y+292), author, 18, 102)
        text(img, (x+178, y+292), progress, 17, 68, 'rt')
    d.line((34, 999, 650, 999), fill=221)
    icon(img, 'CHEVRON_LEFT', 259, 1037, 24, 153)
    text(img, (342, 1021), '1 / 1', 22, 85, 'mt')
    icon(img, 'CHEVRON_RIGHT', 425, 1037, 24, 153)
    return img


def reader_floating_tools(marked=False):
    img=base(True)
    d=ImageDraw.Draw(img)
    d.rectangle((0,1096,W-1,H-1),fill=255)
    d.rounded_rectangle((12,1107,671,1202),48,fill=136)
    d.rounded_rectangle((12,1104,671,1199),48,fill=204)
    d.rounded_rectangle((13,1105,670,1198),47,outline=255)
    tools=[('LIST','Mục lục'),('BOOKMARK_CHECK' if marked else 'BOOKMARK','Đã lưu dấu' if marked else 'Đánh dấu'),
           ('ROTATE_CW','Đồng bộ'),('CHART_COLUMN','Thống kê'),('BOOK_OPEN','Cài đặt đọc'),('TYPE','Phông chữ')]
    for i,(name,label) in enumerate(tools):
        left=i*W//6;right=(i+1)*W//6;cx=(left+right)//2
        if i==1 and marked:
            d.rounded_rectangle((left+12,1112,right-13,1191),40,fill=153)
            d.rounded_rectangle((left+13,1113,right-14,1190),39,outline=255)
        icon(img,name,cx,1138,40)
        px=20
        while font(px).getlength(label)>right-left-8: px-=1
        text(img,(cx,1167),label,px,anchor='mt')
    return quantize(img)


def controls(img, reader=False):
    d = ImageDraw.Draw(img)
    if reader:
        text(img, (62, 893), 'Tuỳ chỉnh trang đọc', 26)
        icon(img, 'X', 613, 910, 24)
        items = [('LIST', 'Mục lục'), ('BOOKMARK', 'Đánh dấu'), ('TYPE', 'Phông chữ'), ('REFRESH_CW', 'Toàn màn')]
        for i, (name, label) in enumerate(items):
            x = 119+i*149
            icon(img, name, x, 981, 36)
            text(img, (x, 1015), label, 20, anchor='mt')
        text(img, (62, 1080), 'Aa', 23)
        d.rounded_rectangle((121, 1090, 560, 1096), 3, fill=170)
        d.rounded_rectangle((121, 1090, 335, 1096), 3, fill=17)
        d.ellipse((324, 1081, 346, 1103), fill=255, outline=17, width=2)
        text(img, (608, 1080), '26', 23, anchor='rt')
        return
    items = [('WIFI', 'Wi-Fi'), ('BLUETOOTH', 'Bluetooth'), ('REFRESH_CW', 'Toàn màn'), ('LOCK', 'Khoá'), ('LIGHTBULB', 'Đèn')]
    for i, (name, label) in enumerate(items):
        x = 91+i*125
        if i in (0, 4):
            d.rounded_rectangle((x-43, 112, x+43, 194), 27, fill=34)
        icon(img, name, x, 152, 37, 255 if i in (0, 4) else 0)
        text(img, (x, 207), label, 18, anchor='mt')
    for y, name, pos in [(267, 'SUN', 360), (324, 'THERMOMETER', 260)]:
        icon(img, name, 65, y, 25)
        d.rounded_rectangle((103, y-4, 601, y+4), 4, fill=170)
        d.rounded_rectangle((103, y-4, pos, y+4), 4, fill=34)
        d.ellipse((pos-12, y-12, pos+12, y+12), fill=255, outline=34, width=2)
    d.rounded_rectangle((316, 355, 368, 359), 2, fill=119)


def quantize(img):
    return img.point([min(15, (v+8)//17)*17 for v in range(256)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'docs/local/glass-previews')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    variants = [('01-frosted', 'A · Frosted', 82, 30), ('02-balanced', 'B · Balanced', 62, 75), ('03-clear', 'C · Clear', 38, 140)]
    renders = []
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        body = re.sub(r'^#include[^\n]*\n', '', (ROOT/'main/ui/ui_glass.c').read_text(), flags=re.M)
        (path/'glass.c').write_text(HOST+body+MAIN)
        exe = path/'glass'
        subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-I'+str(ROOT/'main'), str(path/'glass.c'), str(ROOT/'main/ui/ui_image_dither.c'), '-lm', '-o', str(exe)], check=True)
        for filename, label, white, refract in variants:
            img = glass(exe, base(), (18, 88, 648, 280), white, refract)
            controls(img)
            img = quantize(img)
            img.save(args.output/(filename+'.png'))
            renders.append((label, img))
        img = glass(exe, base(True), (28, 867, 628, 266), 78, 45)
        controls(img, True)
        img = quantize(img)
        img.save(args.output/'04-reader-toolbar.png')
        renders.append(('D · Reader toolbar', img))
        floating = []
        for i, label in [(0, 'Home selected'), (1, 'Books selected'), (3, 'Settings selected')]:
            img = floating_navigation(exe, i)
            img.save(args.output/f'float-nav-{i}.png')
            floating.append((label, img))
        nav_sheet = Image.new('RGB', (1130, 760), '#eeeeec')
        nd = ImageDraw.Draw(nav_sheet)
        for i, (label, img) in enumerate(floating):
            x = 24+i*366
            nd.text((x, 20), label, font=font(23), fill='#202020')
            nav_sheet.paste(img.resize((342, 608), Image.Resampling.LANCZOS), (x, 66))
            crop = img.crop((0, 1064, W, H)).resize((342, 76), Image.Resampling.LANCZOS)
            nav_sheet.paste(crop, (x, 680))
        nav_sheet.save(args.output/'floating-menu-comparison.png')
        pages = [('05-library', 'Thư viện', library_page(), 1),
                 ('06-settings', 'Cài đặt', settings_page(), 3),
                 ('07-display-settings', 'Cài đặt · Hiển thị', settings_page(True), 3)]
        page_sheet = Image.new('RGB', (1130, 730), '#eeeeec')
        pd = ImageDraw.Draw(page_sheet)
        for i, (filename, label, page, active) in enumerate(pages):
            img = floating_navigation(exe, active, page)
            img.save(args.output/(filename+'.png'))
            x = 24+i*366
            pd.text((x, 20), label, font=font(24), fill='#202020')
            page_sheet.paste(img.resize((342, 608), Image.Resampling.LANCZOS), (x, 65))
        pd.text((24, 695), 'LAYOUT PREVIEW · 684 × 1216 · 16 gray levels · Not a device capture', font=font(18), fill='#555555')
        page_sheet.save(args.output/'pages-comparison.png')
        reader_sheet=Image.new('RGB',(764,730),'#eeeeec')
        rd=ImageDraw.Draw(reader_sheet)
        for i,marked in enumerate((False,True)):
            img=reader_floating_tools(marked)
            img.save(args.output/('09-reader-bookmark-active.png' if marked else '08-reader-floating-tools.png'))
            x=24+i*366
            rd.text((x,20),'Đã lưu dấu trang' if marked else 'Menu vuốt lên',font=font(24),fill='#202020')
            reader_sheet.paste(img.resize((342,608),Image.Resampling.LANCZOS),(x,65))
        rd.text((24,695),'LAYOUT PREVIEW · 684 × 1216 · 16 gray levels',font=font(18),fill='#555555')
        reader_sheet.save(args.output/'reader-floating-comparison.png')
    sheet = Image.new('RGB', (4*366+32, 770), '#eeeeec')
    draw = ImageDraw.Draw(sheet)
    for i, (label, img) in enumerate(renders):
        x = 24+i*366
        draw.text((x, 22), label, font=font(23), fill='#202020')
        sheet.paste(img.resize((342, 608), Image.Resampling.LANCZOS), (x, 70))
        draw.text((x, 698), '684 × 1216 · 16 gray levels', font=font(16), fill='#555555')
    draw.text((24, 742), 'DESIGN PREVIEW · Real firmware glass raster + concept layouts · Not a device capture', font=font(16), fill='#555555')
    sheet.save(args.output/'comparison.png')
    (args.output/'parameters.json').write_text(json.dumps({'renderer': 'main/ui/ui_glass.c', 'size': [W, H], 'levels': 16, 'variants': variants, 'reader': {'white': 78, 'refract': 45}, 'note': 'Concept layouts. Optical output and refresh latency require device testing.'}, indent=2)+'\n')
    print(args.output/'comparison.png')


if __name__ == '__main__':
    main()
