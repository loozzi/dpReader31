#!/usr/bin/env python3
"""Exercise the actual S31 system-page routing with a persistent optical footer."""
from pathlib import Path
import subprocess
import tempfile
from home_cover_cache_host_test import function

root = Path(__file__).resolve().parents[1]
source = function('app_present_impl', root/'main/app/app_loop.c')
# Execute the actual early S31 route, including its returns, without unrelated loop services.
end = '        LATENCY_PRESENT_DONE();\n        return;\n    }'
source = source[:source.index(end)+len(end)]
source = source.replace('#if DPREADER_BOARD_METALIO47\n', '') + '\n assert(0);\n}\n'
unit = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define DPREADER_BOARD_METALIO47 1
#include "ui/ui_nav_layout.h"
enum {APP_REDRAW_NONE,APP_REDRAW_AREA,APP_REDRAW_PAGE,APP_REDRAW_FULL,APP_REDRAW_DONE};
enum {EPD_DRAW_SUCCESS,EPD_DRAW_FAILED_ALLOC};
enum {APP_MAIN_REFRESH_NORMAL,APP_MAIN_REFRESH_FAST,APP_MAIN_REFRESH_WATER};
enum {E0470_TURN_LTR,E0470_TURN_RTL,E0470_TURN_TTB,E0470_TURN_BTT};
enum {MODE_DU};
typedef int app_redraw_t;
typedef int e0470_turn_dir_t;
typedef struct {int x,y,width,height;} EpdRect;
/* Function uses the tagged error enum. */
'''
unit = unit.replace('enum {EPD_DRAW_SUCCESS,EPD_DRAW_FAILED_ALLOC};', 'enum EpdDrawError {EPD_DRAW_SUCCESS,EPD_DRAW_FAILED_ALLOC};')
unit += r'''
static uint8_t target[1216],panel[1216];
typedef struct {bool request_back_ripple;uint8_t *fb;void *hl;} app_ctx_t;
typedef struct app_desc {bool binary_ui;void (*render)(app_ctx_t*,uint8_t*);} app_desc_t;
static const app_desc_t *s_presented_main;
static bool s_reader_to_home_water,s_pop_menu_water,nav;
static int policy,body_calls,nav_calls,full_calls,finished,guarded,fail,rendered;
static bool navigation_page_ready(app_ctx_t*c,const app_desc_t*a){(void)c;(void)a;return nav;}
static int app_settings_main_refresh_mode(void){return policy;}
static bool app_settings_main_fast_refresh(void){return policy==APP_MAIN_REFRESH_FAST;}
static void main_present_finished(app_ctx_t*c,const app_desc_t*a,app_redraw_t r){(void)c;(void)a;(void)r;++finished;}
static void ui_click_feedback_reset(void){}
static void ui_click_feedback_begin(uint8_t*f){(void)f;}
static void display_main_transition_cancel(void){}
static void ui_text_set_system_scale(bool b){assert(b);}
static bool display_page_prepare_begin(void){return false;}
static void display_page_prepare_end(bool b){assert(!b);}
static int epd_rotated_display_width(void){return 684;}
static int epd_rotated_display_height(void){return 1216;}
static const void *display_main_bw_waveform(void){return target;}
static void guard_draw_result(void*h,enum EpdDrawError e){(void)h;assert(e==(fail?EPD_DRAW_FAILED_ALLOC:EPD_DRAW_SUCCESS));++guarded;}
static enum EpdDrawError update_display_full(void*h){(void)h;++full_calls;memcpy(panel,target,sizeof(panel));return EPD_DRAW_SUCCESS;}
static enum EpdDrawError body(EpdRect a,bool gray){
 assert(a.x==0&&a.y==0&&a.width==684&&a.height==(nav?1088:1216));
 ++body_calls;if(fail==1)return EPD_DRAW_FAILED_ALLOC;
 /* DU cannot recreate the intermediate gray targets. */
 for(int y=0;y<a.height;++y)panel[y]=gray?target[y]:(target[y]>127?255:0);
 return EPD_DRAW_SUCCESS;
}
static enum EpdDrawError update_display_water_turn(void*h,EpdRect a,int d){(void)h;(void)d;return body(a,true);}
static enum EpdDrawError update_display_area_diff_with(void*h,const void*w,int m,EpdRect a){(void)h;assert(w==target&&m==MODE_DU);return body(a,false);}
static enum EpdDrawError update_display_gray_transition(void*h,EpdRect a){
 (void)h;if(a.y==0)return body(a,true);++nav_calls;assert(a.x==0&&a.y==1088&&a.width==684&&a.height==128);
 if(fail==2)return EPD_DRAW_FAILED_ALLOC;
 memcpy(panel+a.y,target+a.y,a.height);return EPD_DRAW_SUCCESS;
}
static void render(app_ctx_t*c,uint8_t*f){assert(c->fb==f);++rendered;}
'''
unit += source + r'''
int main(void){
 app_desc_t old={false,render},app={true,render};app_ctx_t ctx={false,target,NULL};
 for(policy=0;policy<3;++policy)for(int returning=0;returning<2;++returning)
 for(int root=0;root<2;++root)for(int redraw=APP_REDRAW_PAGE;redraw<=APP_REDRAW_FULL;++redraw){
  for(int old_tab=0;old_tab<4;++old_tab)for(int tab=0;tab<4;++tab){
   body_calls=nav_calls=full_calls=finished=guarded=rendered=0;fail=0;nav=root;
   ctx.request_back_ripple=returning;s_presented_main=&old;
   memset(panel,255,sizeof(panel));memset(target,0,sizeof(target));if(policy!=APP_MAIN_REFRESH_FAST)target[333]=153;
   for(int y=1088;y<1216;++y){panel[y]=(y%4==old_tab)?153:204;target[y]=(y%4==tab)?153:204;}
   app_present_impl(&ctx,&app,redraw);
   assert(rendered==1&&finished==1&&guarded==1);
   assert(nav_calls==(root&&redraw==APP_REDRAW_PAGE));
   assert(full_calls==(redraw==APP_REDRAW_FULL));
   assert(body_calls==(redraw==APP_REDRAW_PAGE));
   if(root||redraw==APP_REDRAW_FULL)assert(!memcmp(panel,target,sizeof(panel)));
  }
 }
 app.binary_ui=false;nav=true;
 for(policy=0;policy<3;++policy){
  body_calls=nav_calls=0;ctx.request_back_ripple=true;
  memset(panel,255,sizeof(panel));memset(target,153,sizeof(target));
  memset(target,0,1088);app_present_impl(&ctx,&app,APP_REDRAW_PAGE);
  assert(body_calls==1&&nav_calls==1&&!memcmp(panel,target,sizeof(panel)));
 }
 app.binary_ui=true;
 nav=true;policy=0;
 for(fail=1;fail<=2;++fail){
  body_calls=nav_calls=0;ctx.request_back_ripple=false;
  app_present_impl(&ctx,&app,APP_REDRAW_PAGE);
  assert(body_calls==1&&nav_calls==(fail==2));
 }
 puts("PASS: actual S31 system route, 16 tab pairs, normal/fast/water, roots/children, edge returns, full refresh and body/footer failures; entire gray footer restored through row1215");
}
'''
with tempfile.TemporaryDirectory() as folder:
    p=Path(folder);(p/'test.c').write_text(unit)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(root/'main'),str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
