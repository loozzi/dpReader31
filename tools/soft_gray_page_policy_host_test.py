#!/usr/bin/env python3
"""Actual Files/WiFi render policy and bounded upload/gray feedback routes."""
from pathlib import Path
import subprocess,tempfile
from home_cover_cache_host_test import function
r=Path(__file__).resolve().parents[1]
files=r/'main/apps/app_files.c';transfer=r/'main/apps/app_transfer.c'
unit=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define DPREADER_BOARD_METALIO47 1
#define UI_GRAY_WHITE 255
#define UI_GRAY_BLACK 0
#define EPD_DRAW_ALIGN_CENTER 1
#define EPD_DRAW_ALIGN_LEFT 0
#define UI_LOCK_WIDTH 684
#define MODE_DU 1
#define MODE_GL16 5
typedef struct{int x,y,width,height;}EpdRect;
typedef struct{uint8_t*fb;void*hl;}app_ctx_t;
typedef int app_redraw_t;
enum{APP_REDRAW_NONE,APP_REDRAW_AREA,APP_REDRAW_PAGE,APP_REDRAW_FULL};
enum{TRANSFER_HOME,TRANSFER_NETWORKS,TRANSFER_METHODS,TRANSFER_PASSWORD};
static bool fast,root,s_render_secondary,s_bulk_delete_confirm,s_wifi_settings_only;
static bool s_progress_pending,s_input_settle,s_input_layout,s_settle;
static char s_bulk_delete_dir[288];static int s_view;
static int paints,monos,navtab,gray,bw,full,errors,error;
static EpdRect s_area,last;
static uint8_t frame[684*1216],saved[684*1216];
static int E0470_WAVEFORM,E0470_FOLLOW_WAVEFORM;
static bool app_settings_main_fast_refresh(void){return fast;}
static bool main_page_visible(app_ctx_t*c){(void)c;return root;}
static void render_content(app_ctx_t*c,uint8_t*fb){assert(c->fb==fb);++paints;memset(fb,221,sizeof(frame));}
static void display_monochrome_content(uint8_t*fb){++monos;for(unsigned i=0;i<sizeof(frame);++i)fb[i]=fb[i]>=128?255:0;}
static void transfer_navigation(uint8_t*fb,int tab){assert(fb==frame);navtab=tab;}
static void ui_fill_round_rect(uint8_t*f,EpdRect a,int rad,int ink){(void)f;(void)a;(void)rad;(void)ink;assert(false);}
static void ui_draw_control_frame(uint8_t*f,EpdRect a,int rad,int ink){(void)f;(void)a;(void)rad;(void)ink;assert(false);}
static void ui_text_box(uint8_t*f,EpdRect a,int px,const char*t,int align,bool inv){(void)f;(void)a;(void)px;(void)t;(void)align;(void)inv;assert(false);}
static void ui_text_caption(uint8_t*f,EpdRect a,int px,const char*t,int align,bool inv){ui_text_box(f,a,px,t,align,inv);}
static void ui_draw_button(uint8_t*f,EpdRect a,const char*t,bool on){(void)f;(void)a;(void)t;(void)on;assert(false);}
static uint8_t ui_read_pixel(const uint8_t*f,int x,int y){assert(x>=0&&x<684&&y>=0&&y<1216);return f[y*684+x]>>4;}
static void epd_draw_pixel(int x,int y,uint8_t ink,uint8_t*f){assert(x>=0&&x<684&&y>=0&&y<1216);f[y*684+x]=ink;}
static const int*display_main_bw_waveform(void){return &E0470_WAVEFORM;}
static int update_display_area_diff_with(void*h,const int*w,int mode,EpdRect a){(void)h;(void)w;assert(mode==MODE_DU||mode==MODE_GL16);++bw;last=a;return error;}
static int update_display_area_full_with(void*h,const int*w,int mode,EpdRect a){(void)h;(void)w;assert(mode==MODE_GL16);++full;last=a;return error;}
static int update_display_gray_transition(void*h,EpdRect a){(void)h;assert(!fast);++gray;last=a;return error;}
static int update_display_area_with(void*h,const int*w,int mode,EpdRect a){return update_display_area_diff_with(h,w,mode,a);}
static void guard_draw_result(void*h,int e){(void)h;assert(e==error);errors+=e!=0;}
'''
unit+=function('render',files).replace('static void render(', 'static void files_render(')+'\n'
unit+=function('render',transfer).replace('static void render(', 'static void transfer_render(')+'\n'
unit+='\n'.join(function(n,transfer) for n in ['status_rect','progress_rect','progress_binary','present'])
unit+=r'''
int main(void){
 app_ctx_t ctx={frame,NULL};
 for(int mode=0;mode<3;++mode)for(int child=0;child<2;++child){
  fast=mode==1;root=!child;s_render_secondary=false;
  int before=monos;files_render(&ctx,frame);
  assert(monos==before+fast&&!s_render_secondary);
  for(unsigned i=0;i<sizeof(frame);++i)assert(frame[i]==(fast?255:221));
  s_wifi_settings_only=child;before=monos;transfer_render(&ctx,frame);
  assert(monos==before+fast&&navtab==(child?3:2));
  for(unsigned i=0;i<sizeof(frame);++i)assert(frame[i]==(fast?255:221));
 }
 for(unsigned i=0;i<sizeof(frame);++i)frame[i]=(uint8_t)(i%256);
 memcpy(saved,frame,sizeof(frame));progress_binary(frame);EpdRect p=progress_rect();
 for(int y=0;y<1216;++y)for(int x=0;x<684;++x){
  int i=y*684+x;bool inside=x>=p.x&&x<p.x+p.width&&y>=p.y&&y<p.y+p.height;
  assert(frame[i]==(inside?(saved[i]>=128?255:0):saved[i]));
 }
 for(int mode=0;mode<3;++mode)for(int fail=0;fail<2;++fail){
  fast=mode==1;error=fail;s_area=p;s_view=TRANSFER_HOME;s_progress_pending=true;
  int g=gray,b=bw;assert(present(&ctx,APP_REDRAW_AREA));
  assert(gray==g&&bw==b+1&&s_progress_pending==!!fail);
  for(s_view=TRANSFER_NETWORKS;s_view<=TRANSFER_METHODS;++s_view){
   g=gray;b=bw;s_settle=false;assert(present(&ctx,APP_REDRAW_AREA));
   assert(gray==g+!fast&&bw==b+fast);
  }
  s_view=TRANSFER_PASSWORD;s_input_settle=false;g=gray;b=bw;
  assert(present(&ctx,APP_REDRAW_AREA)&&gray==g&&bw==b+1);
  s_input_settle=true;g=gray;b=full;
  assert(present(&ctx,APP_REDRAW_AREA)&&gray==g&&full==b+1&&!s_input_settle);
 }
 assert(!present(&ctx,APP_REDRAW_PAGE));
 puts("PASS: actual Files/WiFi root/child renders retain gray outside Fast; upload threshold changes only564x150 live area; uploadDU/error retry,password keys and gray WiFi feedback preserve their scopes");
}
'''
with tempfile.TemporaryDirectory() as folder:
 p=Path(folder);(p/'test.c').write_text(unit)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
