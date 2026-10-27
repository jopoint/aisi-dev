// Isolated WebGL2 compile/visual check. No TD connection, OSC or desktop access.
const {chromium}=require('playwright');
const fs=require('fs'), path=require('path'), assert=require('assert/strict');
(async()=>{
  const dir=process.argv[2], shaders=JSON.parse(fs.readFileSync(path.join(dir,'shaders.json'),'utf8'));
  const browser=await chromium.launch({headless:true,channel:'msedge'});
  try {
    const page=await browser.newPage({viewport:{width:1000,height:1000}});
    await page.setContent('<style>body{margin:0}canvas{display:block}</style><canvas width="1000" height="1000"></canvas>');
    const report=await page.evaluate(shaders=>{
      const canvas=document.querySelector('canvas');
      const gl=canvas.getContext('webgl2',{alpha:true,premultipliedAlpha:false,preserveDrawingBuffer:true});
      if(!gl)throw Error('WebGL2 unavailable');
      function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
      const vertex=shader(gl.VERTEX_SHADER,'#version 300 es\nprecision highp float; out vec3 vUV; void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2); vUV=vec3(p,0);gl_Position=vec4(p*2.-1.,0,1);}');
      function program(source){const fragment=shader(gl.FRAGMENT_SHADER,'#version 300 es\nprecision highp float; precision highp int; uniform sampler2D sTD2DInputs[1]; in vec3 vUV; vec4 TDOutputSwizzle(vec4 v){return v;}\n'+source);const p=gl.createProgram();gl.attachShader(p,vertex);gl.attachShader(p,fragment);gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));return p;}
      const old=program(shaders.old),next=program(shaders.new);
      const state=new Float32Array(6*6*4);
      const set=(row,col,value)=>state.set(value,(row*6+col)*4);
      set(0,0,[210,250,78,1]);set(0,1,[285,300,120,1]);set(0,2,[1,1,.55,0]);
      set(0,3,[0,0,0,1]);set(0,4,[160,80,6,0]);set(0,5,[1,1,0,0]);set(5,0,[4,4,1,1]);
      gl.activeTexture(gl.TEXTURE0);const texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);
      gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA32F,6,6,0,gl.RGBA,gl.FLOAT,state);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
      function render(p,surface){gl.useProgram(p);gl.uniform1i(gl.getUniformLocation(p,'sTD2DInputs[0]'),0);gl.uniform4f(gl.getUniformLocation(p,'uSurface'),surface,0,0,0);gl.drawArrays(gl.TRIANGLES,0,3);const a=new Uint8Array(1000*1000*4);gl.readPixels(0,0,1000,1000,gl.RGBA,gl.UNSIGNED_BYTE,a);return a;}
      const before=render(old,0),after=render(next,0);
      let removed=0,retained=0;
      for(let i=3;i<after.length;i+=4){if(before[i]>250&&after[i]<5)removed++;if(after[i]>250)retained++;}
      if(removed<5000||retained<1000)throw Error('No open dashed floor target');
      render(next,2);
      if(gl.getError()!==gl.NO_ERROR)throw Error('WebGL error');
      return {removed,retained,png:canvas.toDataURL('image/png')};
    },shaders);
    assert(report.removed>5000);
    fs.writeFileSync(path.join(dir,'dashed_preview.png'),Buffer.from(report.png.split(',')[1],'base64'));
    console.log('OFFLINE WEBGL OK: '+JSON.stringify({removed:report.removed,retained:report.retained}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
