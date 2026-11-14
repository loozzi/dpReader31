#!/usr/bin/env python3
"""Sample-data layout previews of reader panels; not device captures.

Run: python3 tools/render_reader_children_previews.py
"""
from PIL import Image, ImageDraw
from render_glass_previews import W, H, base, text, icon, quantize
from render_soft_gray_previews import OUT, card, fit


def sheet(title, top=580):
    img = base(True)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, top, W-1, H+28), 28, fill=255)
    d.rounded_rectangle((292, top+14, 391, top+20), 3, fill=68)
    text(img, (342, top+40), title, 30, anchor='mt')
    return img


def done(img):
    card(img, (36, 1141, 612, 58), 20, True)
    text(img, (342, 1153), 'Xong', 28, anchor='mt')


def reading():
    img = sheet('Cài đặt đọc sách')
    rows = [('Làm mới toàn trang', 'Mỗi 10 trang'),
            ('Hiệu ứng lật trang', 'Thường'),
            ('Chế độ lật trang', 'Trái / phải'),
            ('Lật trang bằng nút nguồn', 'Tắt'),
            ('Điều khiển phím', 'Tùy chỉnh 3 phím'),
            ('Ẩn ảnh minh họa', 'Tắt'),
            ('Chữ dọc (Phải sang trái)', 'Tắt'),
            ('Status & Footer', 'Đầu và chân trang')]
    for i, (label, value) in enumerate(rows):
        x, y = 36+(i % 2)*314, 702+(i//2)*104
        card(img, (x, y, 298, 98), 20)
        fit(img, (x+21, y+10), label, 23, 256)
        fit(img, (x+21, y+53), value, 26, 222)
        if i in (3, 5, 6):
            d = ImageDraw.Draw(img)
            d.rounded_rectangle((x+209, y+54, x+277, y+92), 19, fill=187)
            d.ellipse((x+213, y+57, x+245, y+89), fill=255, outline=119)
        else:
            icon(img, 'CHEVRON_RIGHT', x+272, y+73, 26)
    done(img)
    return img


def fonts():
    img = sheet('Cài đặt phông chữ')
    card(img, (36, 700, 612, 76), 18)
    text(img, (54, 722), 'Cỡ chữ đọc sách', 23)
    text(img, (590, 722), '26', 23, anchor='rt')
    icon(img, 'CHEVRON_RIGHT', 624, 738, 24)
    rows = [('Bộ phông chữ đọc sách', 'Bitter Regular'),
            ('Độ đậm chữ', 'Chuẩn'), ('Bố cục dàn trang', 'Căn lề · Giãn dòng'),
            ('Tùy chỉnh', 'Hiển thị nâng cao')]
    for i, (label, value) in enumerate(rows):
        x, y = 36+(i % 2)*314, 796+(i//2)*132
        card(img, (x, y, 298, 116 if i < 2 else 110), 20)
        fit(img, (x+21, y+12), label, 23, 256)
        fit(img, (x+21, y+63), value, 27, 222)
        icon(img, 'CHEVRON_RIGHT', x+275, y+83, 26)
    done(img)
    return img


def stats():
    img = sheet('Thống kê đọc sách', 506)
    icon(img, 'ARROW_LEFT', 64, 563, 38)
    for i, (value, label) in enumerate([('42%', 'Tiến độ đọc'), ('28 phút', 'Phiên đọc này'), ('56 lần', 'Lật trang')]):
        cx = 114+i*228
        card(img, (cx-100, 602, 200, 98), 18)
        text(img, (cx, 612), value, 33, anchor='mt')
        text(img, (cx, 664), label, 20, anchor='mt')
    text(img, (54, 710), 'Tiến độ sách', 21)
    text(img, (630, 710), '42%', 19, anchor='rt')
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((54, 746, 630, 757), 6, fill=204)
    d.rounded_rectangle((54, 746, 296, 757), 6, fill=68)
    text(img, (54, 804), 'Chuyển trang', 23)
    text(img, (630, 804), 'Truyện Kiều', 19, anchor='rt')
    card(img, (54, 854, 402, 72), 36)
    text(img, (91, 871), '−', 32, anchor='mt')
    text(img, (255, 877), 'Trang 42 / 168', 26, anchor='mt')
    text(img, (419, 871), '+', 32, anchor='mt')
    card(img, (476, 854, 154, 72), 36, True)
    text(img, (553, 878), 'Chuyển', 24, anchor='mt')
    text(img, (54, 946), 'Trang hiện tại: 42 (chạm số để nhập trang)', 18)
    for i, label in enumerate(['Dấu trang · 3', '30 ngày qua', 'Đồng bộ KOSync']):
        x = 36+i*208
        card(img, (x, 986, 196, 78), 20)
        text(img, (x+98, 1011), label, 21, anchor='mt')
    card(img, (36, 1072, 612, 72), 18)
    icon(img, 'LIST', 72, 1108, 28)
    text(img, (374, 1091), 'Danh sách ghi chú', 27, anchor='mt')
    return img


def toc():
    img = Image.new('L', (W, H), 255)
    img.paste(base().crop((0, 0, W, 60)), (0, 0))
    icon(img, 'ARROW_LEFT', 58, 114, 48)
    text(img, (342, 96), 'Mục lục', 34, anchor='mt')
    text(img, (36, 172), 'Truyện Kiều', 23)
    text(img, (648, 172), '21 mục', 23, anchor='rt')
    for i, label in enumerate(['Gia thế Thúy Kiều', 'Gặp gỡ Kim Trọng', 'Đính ước', 'Gia biến',
                               'Kiều bán mình', 'Mã Giám Sinh', 'Lầu Ngưng Bích']):
        y = 252+i*108
        card(img, (36, y, 612, 94), 20, i == 1)
        text(img, (50, y+31), f'{i+1:02}', 21)
        fit(img, (115, y+26), label, 30, 420)
        if i == 1:
            text(img, (626, y+33), 'Hiện tại', 20, anchor='rt')
    for x, width, label in [(36, 100, '« 10 tr'), (146, 112, '‹ Trước'),
                            (268, 148, '1 / 3'), (426, 112, 'Sau ›'), (548, 100, '10 tr »')]:
        card(img, (x, 1018, width, 68), 20, x == 268)
        text(img, (x+width//2, 1038), label, 24, anchor='mt')
    card(img, (36, 1100, 612, 74), 21)
    text(img, (58, 1125), 'Chuyển theo phần trăm (%)', 28)
    text(img, (628, 1125), '0%', 27, anchor='rt')
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    composite = Image.new('RGB', (W*2+72, H*2+128), '#e4e4e1')
    for i, (name, draw) in enumerate([('Mục lục', toc), ('Cài đặt đọc', reading),
                                      ('Phông chữ', fonts), ('Thống kê', stats)]):
        img = quantize(draw())
        img.save(OUT/f'reader-child-{i+1}.png')
        x, y = 24+(i % 2)*(W+24), 38+(i//2)*(H+48)
        ImageDraw.Draw(composite).text((x, y-27), name, fill='#222222')
        composite.paste(img, (x, y))
    composite.resize((720, 1280), Image.Resampling.LANCZOS).save(OUT/'reader-children.png')
    print(OUT/'reader-children.png')


if __name__ == '__main__':
    main()
