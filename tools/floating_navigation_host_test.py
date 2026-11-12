#!/usr/bin/env python3
"""中文：悬浮导航实际绘制、跨页反馈和灰阶推屏检查。/ English: Actual floating navigation, cross-page feedback and gray presentation checks.

Run in the metalio47 host view generated with board_source_view.py --tests.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from home_cover_cache_host_test import function

ROOT = Path(__file__).resolve().parents[1]

DRAW = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "assets/ui_icons.h"
#include "ui/ui_nav_layout.h"
#define UI_LOCK_WIDTH 684
#define UI_LOCK_HEIGHT 1216
#define UI_GRAY_WHITE 255
#define UI_GRAY_BLACK 0
#define EPD_DRAW_ALIGN_CENTER 1
#define UI_NAV_TAB_ICON_PX 44
#define UI_TOUCH_SLOP_PX 24
#define MALLOC_CAP_SPIRAM 1
#define MALLOC_CAP_8BIT 2
enum {EPD_ROT_LANDSCAPE,EPD_ROT_PORTRAIT,EPD_ROT_INVERTED_LANDSCAPE,EPD_ROT_INVERTED_PORTRAIT};
typedef struct {int x,y,width,height;} EpdRect;
typedef enum {UI_CLICK_NAV,UI_CLICK_BACK,UI_CLICK_BACK_SMALL} ui_click_kind_t;
static bool simple,oom;
static int live,texts;
static uint8_t frame[684*1216],baseline[684*1216];
static bool app_settings_simple_ui(void){return simple;}
static bool app_settings_main_fast_refresh(void){return false;}
static int epd_get_rotation(void){return EPD_ROT_LANDSCAPE;}
static int epd_width(void){return 684;}
static int epd_height(void){return 1216;}
static int epd_rotated_display_width(void){return 684;}
static int epd_rotated_display_height(void){return 1216;}
static uint8_t epd_get_pixel(int x,int y,int w,int h,const uint8_t *fb){assert(w==684&&h==1216);return fb[y*w+x];}
static void epd_draw_pixel(int x,int y,uint8_t g,uint8_t *fb){assert(x>=0&&x<684&&y>=0&&y<1216);fb[y*684+x]=g;}
static void epd_fill_rect(EpdRect r,uint8_t g,uint8_t *fb){for(int y=0;y<r.height;y++)for(int x=0;x<r.width;x++)epd_draw_pixel(r.x+x,r.y+y,g,fb);}
static void ui_fill_rect_fast(EpdRect r,uint8_t g,uint8_t *fb){epd_fill_rect(r,g,fb);}
static bool inside(EpdRect r,int radius,int x,int y){
 int dx=x<r.x+radius?r.x+radius-x:x>=r.x+r.width-radius?x-(r.x+r.width-radius-1):0;
 int dy=y<r.y+radius?r.y+radius-y:y>=r.y+r.height-radius?y-(r.y+r.height-radius-1):0;
 return dx*dx+dy*dy<=radius*radius;
}
static void ui_fill_round_rect(uint8_t *fb,EpdRect r,int radius,uint8_t g){
 for(int y=r.y;y<r.y+r.height;y++)for(int x=r.x;x<r.x+r.width;x++)if(inside(r,radius,x,y))epd_draw_pixel(x,y,g,fb);
}
static void ui_draw_round_rect(uint8_t *fb,EpdRect r,int radius,uint8_t g){
 EpdRect inner={r.x+1,r.y+1,r.width-2,r.height-2};
 for(int y=r.y;y<r.y+r.height;y++)for(int x=r.x;x<r.x+r.width;x++)if(inside(r,radius,x,y)&&(!inside(inner,radius-1,x,y)||x==r.x||y==r.y||x==r.x+r.width-1||y==r.y+r.height-1))epd_draw_pixel(x,y,g,fb);
}
static void ui_draw_icon(uint8_t *fb,int x,int y,int size,ui_icon_t icon,uint8_t g){(void)icon;epd_fill_rect((EpdRect){x-size/4,y-size/4,size/2,size/2},g,fb);}
static void ui_text(uint8_t *fb,int x,int y,int px,const char *s,int align,bool inv){(void)fb;(void)x;(void)y;(void)px;(void)align;(void)inv;assert(s&&*s);++texts;}
static void ui_image_bw_rect(uint8_t *fb,EpdRect r){(void)fb;(void)r;}
static void *heap_caps_malloc(size_t n,unsigned caps){assert(caps==3&&n<=4096);if(oom)return NULL;void*p=malloc(n);assert(p);++live;return p;}
static void heap_caps_free(void*p){if(p){--live;free(p);}}
static const char *labels[]={"Trang chủ","Kệ sách","Tệp tin","Cài đặt"};
static int ui_nav_hit(uint16_t x,uint16_t y);
'''

CASES = r'''
int main(void){
 for(simple=false;;simple=true){
  for(int tab=0;tab<4;tab++){
   if(simple&&tab!=0&&tab!=3)continue;
   memset(frame,0x33,sizeof(frame));ui_click_feedback_begin(frame);texts=0;ui_nav_draw(frame,tab);
   assert(texts==(simple?2:4)&&!live);
   for(int y=0;y<UI_NAV_REFRESH_END;y++)for(int x=0;x<684;x++)assert(frame[y*684+x]==0x33);
   for(int y=UI_NAV_REFRESH_END;y<UI_NAV_TOP+8;y++)for(int x=0;x<684;x++)assert(frame[y*684+x]==255);
   for(int y=UI_NAV_REFRESH_END;y<1216;y++)assert(frame[y*684]==255&&frame[y*684+683]==255);
   int slots=simple?2:4;
   for(int i=0;i<slots;i++){
    int id=simple?(i?3:0):i,cx=(2*i+1)*684/(2*slots);
    assert(frame[(UI_NAV_TOP+87)*684+cx]==(id==tab?0xdd:0xee));
    assert(ui_nav_hit(cx,UI_NAV_TOUCH_TOP)==id);
   }
   memcpy(baseline,frame,sizeof(frame));EpdRect dirty;
   int cx=simple?(tab==0?171:513):(2*tab+1)*684/8;
   assert(ui_click_feedback_press(frame,cx,1140,&dirty));
   assert(live==1&&dirty.y>=UI_NAV_REFRESH_END);
   assert(ui_click_feedback_release(frame,&dirty)&&!live&&!memcmp(frame,baseline,sizeof(frame)));
  }
  if(simple)break;
 }
 simple=false;
 assert(ui_nav_hit(684,1140)==-1&&ui_nav_hit(100,UI_NAV_TOUCH_TOP-1)==-1);
 for(int old=0;old<4;old++)for(int next=0;next<4;next++){
  ui_click_feedback_reset();ui_click_feedback_begin(frame);ui_nav_draw(frame,old);
  EpdRect dirty;ui_click_feedback_nav_request(next);assert(ui_click_feedback_nav_tick(frame,0,&dirty)&&live==1);
  ui_click_feedback_begin(frame);assert(!live&&ui_click_feedback_nav_pending());ui_nav_draw(frame,next);
  memcpy(baseline,frame,sizeof(frame));assert(ui_click_feedback_nav_tick(frame,1,&dirty)&&live==1);
  assert(ui_click_feedback_nav_tick(frame,100,&dirty)&&!live&&!memcmp(frame,baseline,sizeof(frame)));
 }
 ui_click_feedback_nav_request(0);oom=true;EpdRect dirty;
 (void)ui_click_feedback_nav_tick(frame,200,&dirty);assert(!live&&!ui_click_feedback_nav_pending());
 ui_click_feedback_reset();
 puts("PASS: actual floating navigation bounds, white guard, all 4/2-tab selections and hit regions; exact press restoration; 16 cross-page feedback baselines; OOM cleanup");
}
'''

PRESENT = r'''
int main(void){
 (void)owner_b;
 for(int mode=0;mode<3;mode++)for(int old=0;old<4;old++)for(int next=0;next<4;next++){
  reset();main_mode=mode;
  // 中文：模拟选中胶囊与图标的真实灰阶迁移。/ English: Simulate real gray transitions in selected pills and icon wells.
  for(int row=0;row<H;row++)for(int x=UI_NAV_REFRESH_END/2;x<W/2;x++){
   back[row*W/2+x]=panel[row*W/2+x]=((row/(H/4))==old)?0xdd:0xee;
   front[row*W/2+x]=((row/(H/4))==next)?0xdd:0xee;
  }
  memcpy(final,front,BYTES);display_main_transition_arm(&owner_a,false,true);
  assert(update_display_fast_page(&hl)==EPD_DRAW_SUCCESS);
  if(memcmp(panel,final,BYTES))fprintf(stderr,"navigation mode=%d old=%d next=%d\n",mode,old,next);
  assert_final();
  assert(!bw_calls&&!full_calls&&!allocations);
  assert(gray_calls==(old!=next));
  if(old!=next)assert(last_mode==MODE_GL16&&last_wave==&main_gray&&last_area.y==UI_NAV_REFRESH_END&&last_area.y+last_area.height==W);
  int before=calls;display_main_transition_arm(&owner_a,false,false);
  assert(update_display_fast_page(&hl)==EPD_DRAW_SUCCESS&&calls==before);
 }
 for(int mode=0;mode<3;mode++)for(int fail=0;fail<3;fail++){
  reset();main_mode=mode;target(3);
  for(int row=0;row<H;row++)for(int x=UI_NAV_REFRESH_END/2;x<W/2;x++)front[row*W/2+x]=0xdd;
  memcpy(final,front,BYTES);failures=fail?1:0;fail_after=fail==2?1:0;fail_error=EPD_DRAW_EMPTY_LINE_QUEUE;
  display_main_transition_arm(&owner_a,false,true);
  assert(update_display_fast_page(&hl)==EPD_DRAW_SUCCESS);
  if(memcmp(panel,final,BYTES))fprintf(stderr,"body mode=%d fail=%d\n",mode,fail);
  assert_final();assert(!allocations);
  assert(gray_calls>=1);
 }
 for(int mode=0;mode<3;mode++)for(int low=0;low<2;low++){
  reset();main_mode=mode;alloc_fail=low;target(2);
  for(int row=0;row<H;row++){
   for(unsigned b=0;b<3;b++)for(int x=acrylic[b].y/2;x<(acrylic[b].y+acrylic[b].height)/2;x++)front[row*W/2+x]=(uint8_t)(row%256);
   for(int x=UI_NAV_REFRESH_END/2;x<W/2;x++)front[row*W/2+x]=0xdd;
  }
  memcpy(final,front,BYTES);display_main_transition_arm(&owner_a,false,true);
  display_main_transition_gray_bands(acrylic,3);
  assert(update_display_fast_page(&hl)==EPD_DRAW_SUCCESS);assert_final();
  assert(frees==(mode==APP_MAIN_REFRESH_FAST&&!low));
 }
 reset();main_mode=APP_MAIN_REFRESH_FAST;
 for(int turn=0;turn<8;turn++){
  now_us+=4000000;target(turn);
  for(int row=0;row<H;row++)for(int x=UI_NAV_REFRESH_END/2;x<W/2;x++)front[row*W/2+x]=(turn&1)?0xdd:0xee;
  memcpy(final,front,BYTES);display_main_transition_arm(&owner_a,false,true);
  assert(update_display_fast_page(&hl)==EPD_DRAW_SUCCESS);assert_final();
 }
 assert(gc_calls>=1);
 puts("PASS: real S31 presenter in 3 modes, all 16 pill transitions, unchanged-frame skips, combined body/nav targets, body/nav faults, gray-band OOM fallback and periodic full cleanup; no navigation allocations");
}
'''


def run(tmp, name, source, more=()):
    c = tmp/(name+'.c')
    c.write_text(source)
    exe = tmp/name
    link_gc = '-Wl,-dead_strip' if sys.platform == 'darwin' else '-Wl,--gc-sections'
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function', '-g', '-fsanitize=address,undefined', '-ffunction-sections', '-fdata-sections', link_gc, '-I'+str(ROOT/'tools/display_host_stubs'), '-I'+str(ROOT/'components/continuous_du/include'), '-I'+str(ROOT/'components/e0470_page_turn/include'), '-I'+str(ROOT/'main'), '-I'+str(ROOT/'main/app'), str(c), *map(str, more), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


with tempfile.TemporaryDirectory() as folder:
    tmp = Path(folder)
    feedback = re.sub(r'^#include[^\n]*\n', '', (ROOT/'main/ui/ui_click_feedback.c').read_text(), flags=re.M)
    draw = DRAW+feedback+'\n'+function('ui_nav_hit', ROOT/'main/ui/ui_nav.c')+'\n'+function('icon', ROOT/'main/ui/ui_nav.c')+'\n'+function('ui_nav_draw', ROOT/'main/ui/ui_nav.c')+CASES
    run(tmp, 'floating-draw', draw)
    harness = (ROOT/'tools/display_navigation_host_test.c').read_text().split('int main(void)')[0]
    # 中文：原区域替身的横条扩展范围改为内容截止线；其余波形及内存断言保留。/ English: Region shim now stops at the body boundary rather than extending through the obsolete marker; retain waveform/memory assertions.
    harness = harness.replace('assert(area.y==0 && area.height==UI_NAV_MARKER_SCAN_END);', 'assert(area.y==0 && area.height==UI_NAV_REFRESH_END);')
    run(tmp, 'floating-present', harness+PRESENT, [ROOT/'main/display.c', ROOT/'main/ui/ui_image_dither.c'])
