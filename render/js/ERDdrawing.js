function drawEllipse(ctx, x, y, w, h, color, name) {
  var kappa = .5522848;
      ox = (w / 2) * kappa, // control point offset horizontal
      oy = (h / 2) * kappa, // control point offset vertical
      xe = x + w,           // x-end
      ye = y + h,           // y-end
      xm = x + w / 2,       // x-middle
      ym = y + h / 2;       // y-middle

  ctx.beginPath();
  ctx.moveTo(x, ym);
  ctx.bezierCurveTo(x, ym - oy, xm - ox, y, xm, y);
  ctx.bezierCurveTo(xm + ox, y, xe, ym - oy, xe, ym);
  ctx.bezierCurveTo(xe, ym + oy, xm + ox, ye, xm, ye);
  ctx.bezierCurveTo(xm - ox, ye, x, ym + oy, x, ym);
  ctx.closePath();
  ctx.strokeStyle=color;
  ctx.stroke();
  
  ctx.font="10px Arial";//font of the text in attribute
  ctx.textAlign="center";
  ctx.textBaseline="middle"; 
  ctx.fillStyle=color;
  ctx.fillText(name,x+w/2,y+h/2); 
}

function drawRectangle(ctx, x, y, w, h, color, name){

ctx.strokeStyle=color;
ctx.strokeRect(x,y,w,h);

ctx.font="20px Arial";//font of the text in entity
ctx.textAlign="center";
ctx.textBaseline="middle"; 
ctx.fillStyle=color;
ctx.fillText(name,x+w/2,y+h/2); 
}

function drawDiamond(ctx, x, y, w, h, color, name){
 
 ctx.beginPath();
 ctx.moveTo(x+w/2,y);
 ctx.lineTo(x+w,y+h/2);
 ctx.lineTo(x+w/2,y+h);
 ctx.lineTo(x,y+h/2);
 ctx.closePath();
 ctx.strokeStyle=color;
 ctx.stroke();
 
 ctx.font="20px Arial";//font of the text in relationship
 ctx.textAlign="center";
 ctx.textBaseline="middle"; 
 ctx.fillStyle=color;
 ctx.fillText(name,x+w/2,y+h/2); 
 }
 
 function drawDoubleLineRect(ctx, x, y, w, h, color, name){
 
 //outer rectangle
 ctx.strokeStyle=color;
 ctx.strokeRect(x,y,w,h);
 
 //inner rectangle
 ctx.strokeRect(x+2,y+2,w-4,h-4);
 
 ctx.font="20px Arial";//font of the text in weak entity
 ctx.textAlign="center";
 ctx.textBaseline="middle"; 
 ctx.fillStyle=color;
 ctx.fillText(name,x+w/2,y+h/2);  
 }
 
 // function drawArrow(x1,y1,x2,y2,style,which,angle,length){
 
 // calculate the angle of the line 
 // var lineangle=Math.atan2(y2-y1,x2-x1); 
 // h is the line length of a side of the arrow head 
 // var h=Math.abs(d/Math.cos(angle));
 
 // if(which&1){ // handle head at far end 
 // var angle1=lineangle+Math.PI+angle; 
 // var topx=x2+Math.cos(angle1)*h; 
 // var topy=y2+Math.sin(angle1)*h;
 
 // var angle2=lineangle+Math.PI-angle; 
 // var botx=x2+Math.cos(angle2)*h; 
 // var botx=y2+Math.sin(angle2)*h; 
 // toDrawHead(ctx,topx,topy,x2,y2,botx,boty,style); }
 
 // if(which&2){ // handle head at near end 
 // var angle1=lineangle+angle; 
 // var topx=x1+Math.cos(angle1)*h; 
 // var topy=y1+Math.sin(angle1)*h; 
 // var angle2=lineangle-angle; 
 // var botx=x1+Math.cos(angle2)*h; 
 // var boty=y1+Math.sin(angle2)*h; 
 // ctx.beginPath(); 
 // toDrawHead(ctx,topx,topy,x1,y1,botx,boty,style); }
 // }