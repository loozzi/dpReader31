#!/usr/bin/env python3
"""Real shelf geometry/paging for the user's3x2 soft-gray layout."""
from pathlib import Path
import subprocess
import tempfile
from home_cover_cache_host_test import function
root=Path(__file__).resolve().parents[1]
book=root/'main/apps/app_book.c'
unit=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#define BOOK_GRID_ROWS 9
#define BOOK_BULK_ROWS 6
#define UI_MARGIN 36
#define UI_GAP 12
#define UI_BTN_H 76
#define UI_NAV_REFRESH_END 1088
typedef struct {int x,y,width,height;} EpdRect;
enum {SHELF,READING,TOC,MANAGE,BULK};
static int s_view,style,s_visible_count;
static int app_settings_shelf_style(void){return style;}
static int ui_content_width(void){return 612;}
static int book_navigation_count(void){return 20;}
static int book_toc_pages(int n){return(n+9)/10;}
'''
unit+='\n'.join(function(n,book) for n in ['shelf_rows','row_rect','shelf_cover_image','leaves'])
unit+=r'''
static bool overlap(EpdRect a,EpdRect b){return a.x<b.x+b.width&&b.x<a.x+a.width&&a.y<b.y+b.height&&b.y<a.y+a.height;}
int main(void){
 s_view=SHELF;
 for(style=1;style<=5;++style){
  int count=shelf_rows();assert(count==(style==2?6:style==5?4:9));
  for(int row=0;row<count;++row){
   EpdRect card=row_rect(row),image=shelf_cover_image(row);
   assert(card.x>=36&&card.x+card.width<=648&&card.y>=184&&card.y+card.height<UI_NAV_REFRESH_END);
   assert(image.x>=card.x&&image.x+image.width<=card.x+card.width);
   assert(image.y>=card.y&&image.y+image.height<=card.y+card.height);
   for(int other=0;other<row;++other)assert(!overlap(card,row_rect(other)));
   if(style==2){
    assert(image.width==164&&image.height==214);
    assert(image.y+320<card.y+card.height);
   }
  }
  for(s_visible_count=0;s_visible_count<=100;++s_visible_count){
   int pages=leaves();assert(pages==(s_visible_count?(s_visible_count+count-1)/count:1));
   for(int p=0;p<pages;++p)for(int row=0;row<count;++row){
    int index=p*count+row;if(index>=s_visible_count)continue;
    assert(index>=0&&index<s_visible_count);
   }
  }
 }
 s_view=BULK;assert(shelf_rows()==9);
 puts("PASS: actual six-book3x2 geometry,disjoint hit targets,title/size bounds,original164x214 fast-cover budget,all page counts0..100;dark nine-book/list four-book layouts retained");
}
'''
with tempfile.TemporaryDirectory() as folder:
 p=Path(folder);(p/'test.c').write_text(unit)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
