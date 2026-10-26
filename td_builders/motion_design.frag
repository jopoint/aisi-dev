// AISI v1.5. Shared world-space shader, before any projector warp.
// Horizontal canonical Rect; y points down. Input: six-by-six RGBA state TOP.
layout(location = 0) out vec4 fragColor;
uniform vec4 uSurface; // 0 floor, 1 tabletop, 2 combined preview
const float PI = 3.141592653589793;

vec2 rotate2(vec2 p, float degrees) {
    float a = radians(degrees), c = cos(a), s = sin(a);
    return mat2(c, s, -s, c) * p;
}
vec4 datum(int col, int row) { return texelFetch(sTD2DInputs[0], ivec2(col, row), 0); }
float roundedRect(vec2 p, vec2 halfSize, float r) {
    vec2 q = abs(p) - halfSize + r;
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}
float coverage(float d) { return 1.0 - smoothstep(-.35, .35, d); }
float segment(vec2 p, vec2 a, vec2 b) {
    vec2 ab = b - a;
    return length(p - a - ab * clamp(dot(p-a, ab)/dot(ab, ab), 0.0, 1.0));
}
float arrow(vec2 p) {
    // Exact v1.5 SVG path M -13 0 L 10 0 M 0 -10 L 10 0 L 0 10;
    // width 6, round joins/caps = union of three capsules.
    float d = min(segment(p, vec2(-13,0), vec2(10,0)),
                  min(segment(p, vec2(0,-10), vec2(10,0)),
                      segment(p, vec2(10,0), vec2(0,10))));
    return coverage(d - 3.0);
}
vec4 white(float a) { return vec4(vec3(a), a); }
vec4 over(vec4 front, vec4 back) { return front + back * (1.0-front.a); }
float softRing(float radius, float atRadius) {
    // Smooth Gaussian approximation of the reference's 7 cm stroke + 4 cm blur.
    return exp(-.5 * pow((atRadius-radius)/4.7, 2.0));
}
float radial(float r) {
    if (r < .742857) return mix(1.0, .95, r/.742857);
    if (r < .88) return mix(.95, .3, (r-.742857)/(.88-.742857));
    return mix(.3, 0.0, clamp((r-.88)/.12, 0.0, 1.0));
}
float ellipse(vec2 p, vec2 center, vec2 axes) {
    return radial(length((p-center)/axes));
}
float blurredEllipse(vec2 p, vec2 center, vec2 axes) {
    float b = 4.05;
    float a = ellipse(p,center,axes)*.25;
    a += (ellipse(p+vec2(b,0),center,axes)+ellipse(p-vec2(b,0),center,axes)
        +ellipse(p+vec2(0,b),center,axes)+ellipse(p-vec2(0,b),center,axes))*.125;
    a += (ellipse(p+vec2(b,b),center,axes)+ellipse(p-vec2(b,b),center,axes)
        +ellipse(p+vec2(b,-b),center,axes)+ellipse(p+vec2(-b,b),center,axes))*.0625;
    return a;
}
float feedbackHalo(vec2 offset, float angle, float h, float t, float distance) {
    // User correction to v1.5: positional arrival must be round even when
    // rotation/progress still prevents success. Fade ALL directional terms,
    // including the small time-varying offsets and axis breathing.
    float directional=smoothstep(8.0,29.0,distance);
    float asymmetry=(1.0-h)*(1.0-h)*directional;
    float radius=mix(35.0,81.4,smoothstep(0.0,1.0,h));
    vec2 q=directional==0.0?offset:rotate2(offset,-angle);
    float g1=blurredEllipse(q,vec2(asymmetry*24.0,directional*sin(t*1.8)*1.4),
        radius*vec2(1.0+asymmetry*.22+directional*.04*sin(t*1.6),
                    1.0-asymmetry*.20+directional*.035*sin(t*1.3+.7)));
    float g2=ellipse(q,vec2(asymmetry*19.0,0),
        radius*vec2(1.0,1.0-asymmetry*.22+directional*.035*sin(t*1.4)))*.8;
    return g2+g1*(1.0-g2);
}
float targetEdge(vec2 direction, float rotation, vec2 halfSize, float corner) {
    vec2 d = rotate2(direction,-rotation);
    float lo=0.0, hi=length(halfSize);
    // Ray intersection with the same rounded contour used by contact/rendering.
    for(int j=0;j<16;j++) {
        float mid=(lo+hi)*.5;
        if(roundedRect(d*mid,halfSize,corner)>0.0) hi=mid; else lo=mid;
    }
    return (lo+hi)*.5;
}
void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 clock=datum(0,5);
    if(clock.z<.5) {
        fragColor=TDOutputSwizzle(uSurface.x>1.5?vec4(.188,.282,.247,1):vec4(0));
        return;
    }
    float t=clock.x, reveal=clamp(clock.y/3.0,0.0,1.0), wave=reveal*405.0;
    float released = reveal>=1.0?1.0:coverage(length(p-250.0)-max(0.0,wave-14.0));
    float waveAlpha = (reveal>0.0 && reveal<1.0) ?
        max(coverage(abs(length(p-250.0)-wave)-5.0),
            exp(-.5*pow((length(p-250.0)-wave)/8.0,2.0))*.8) : 0.0;
    vec4 floorColor=vec4(0), tableColor=vec4(0);
    float occupied=0.0;
    for(int i=0;i<5;i++) {
        vec4 source=datum(0,i), target=datum(1,i), state=datum(2,i);
        vec4 pulse=datum(3,i), shape=datum(4,i);
        if(source.w<.5) continue;
        vec2 halfSize=shape.xy*.5;
        float sourceMask=coverage(roundedRect(rotate2(p-source.xy,-source.z),halfSize,shape.z));
        occupied=max(occupied,sourceMask);
        vec4 layer=vec4(0);
        if(target.w>.5 && state.w<1.5) {
            float targetMask=coverage(roundedRect(rotate2(p-target.xy,-target.z),halfSize,shape.z));
            vec2 delta=target.xy-source.xy;
            float distance=length(delta);
            // atan(0,0) is undefined in GLSL. The reference fixes near-target
            // orientation at zero, including while rotation is still outside tolerance.
            float angle=distance<3.0?0.0:degrees(atan(delta.y,delta.x));
            vec2 direction=distance>.001?delta/distance:vec2(1,0);
            vec4 f=white(targetMask);
            if(distance>.001) {
                float edge=targetEdge(-direction,target.z,halfSize,shape.z);
                float arrows=0.0;
                for(int k=0;k<12;k++) {
                    float l=edge+18.0+13.0+float(k)*43.0;
                    if(l>distance) break;
                    arrows=max(arrows,arrow(rotate2(p-(target.xy-direction*l),-angle)));
                }
                arrows *= step(0.0,dot(p-source.xy,direction));
                f=over(white(arrows),f);
            }
            floorColor=over(f*(released*pulse.w),floorColor);
            bool success=state.w>.5;
            layer=white(success?0.0:targetMask);
            float navRadius=29.0*state.x;
            float centerDistance=length(p-source.xy);
            if(success) {
                layer=vec4(0.0,236.0/255.0,101.0/255.0,1.0);
            } else {
                float ga=feedbackHalo(p-source.xy,angle,state.z,t,distance)
                    *smoothstep(0.0,1.0,state.y);
                layer=over(vec4(vec3(0.0,236.0/255.0,101.0/255.0)*ga,ga),layer);
                float ring=softRing(pulse.x,centerDistance)*pulse.y;
                float nav=state.x>0.0?coverage(centerDistance-navRadius):0.0;
                layer=over(white(ring*(1.0-nav)),layer);
                float hole=0.0;
                if(distance>=3.0 && state.x>0.0)
                    hole=arrow(rotate2(p-source.xy,-angle)/state.x-vec2(5,0));
                layer=over(white(nav*(1.0-hole)*(1.0-ring)),layer);
            }
            float dissolve=success ? smoothstep(0.0,1.0,pulse.z)*105.0 : 0.0;
            float remain=success ? smoothstep(-6.0,6.0,length(p-source.xy)-dissolve) : 1.0;
            if(success && pulse.z<=0.0) remain=1.0;
            layer*=sourceMask*released*remain;
        }
        // The global wave also passes over stationary/inactive captured tables.
        layer=over(white(waveAlpha*sourceMask),layer);
        tableColor=over(layer,tableColor);
    }
    floorColor=over(white(waveAlpha),floorColor)*(1.0-occupied);
    if(uSurface.x<.5) fragColor=TDOutputSwizzle(floorColor);
    else if(uSurface.x<1.5) fragColor=TDOutputSwizzle(tableColor);
    else {
        vec4 background=mix(vec4(.188,.282,.247,1),vec4(.647,.647,.647,1),occupied);
        fragColor=TDOutputSwizzle(over(tableColor,over(floorColor,background)));
    }
}
