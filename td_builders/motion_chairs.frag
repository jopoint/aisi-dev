// Synthetic chairs from the same explicitly activated world-space proposal.
layout(location=0) out vec4 fragColor;
vec4 datum(int c,int r) { return texelFetch(sTD2DInputs[0],ivec2(c,r),0); }
float coverage(float d) { return 1.0-smoothstep(-.35,.35,d); }
float rect(vec2 p,vec2 size,float corner) {
    vec2 q=abs(p)-size+corner;
    return length(max(q,0.0))+min(max(q.x,q.y),0.0)-corner;
}
void main() {
    vec4 clock=datum(0,5);
    vec4 visualReveal=datum(1,5);
    if(visualReveal.z>.5) {
        if(visualReveal.y<.5) {
            fragColor=TDOutputSwizzle(vec4(0));
            return;
        }
        clock.y=visualReveal.x;
    }
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    float a=0.0;
    if(clock.z>.5) {
        for(int i=0;i<15;i++) {
            vec4 c=texelFetch(sTD2DInputs[1],ivec2(i,0),0);
            if(c.w>.5) a=max(a,coverage(abs(length(p-c.xy)-(c.z-1.25))-1.25));
        }
        float occupied=0.0;
        for(int i=0;i<5;i++) {
            vec4 s=datum(0,i), shape=datum(4,i);
            float angle=radians(-s.z);
            vec2 q=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*(p-s.xy);
            if(s.w>.5) occupied=max(occupied,coverage(rect(q,shape.xy*.5,shape.z)));
        }
        float reveal=clamp(clock.y/3.0,0.0,1.0);
        float released=reveal>=1.0?1.0:coverage(length(p-250.0)-max(0.0,reveal*405.0-14.0));
        a*=released*(1.0-occupied);
    }
    fragColor=TDOutputSwizzle(vec4(a));
}
