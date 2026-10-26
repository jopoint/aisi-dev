"""Deterministic TD acceptance in a temporary isolated component, then cleanup.

No writes to the running preview, receiver, masks or projector outputs.
"""
import builtins
import json
from pathlib import Path
import sys

REPO=Path('/Users/Johannes/dev/Promotion_Prototypen/AISI')
TEST_NAME='comp_aisi_motion_acceptance'


def check(resolve,symbols):
    import numpy as np
    result={'checks':[],'passed':False,'saved':False,'temporary_component_removed':False}
    root=resolve('/project1')
    if root is None or root.op(TEST_NAME) is not None:
        raise RuntimeError('Test-COMP existiert bereits oder project1 fehlt; nichts verändert.')
    namespace={'__name__':'motion_acceptance_builder','_AISI_MOTION_IMPORT_ONLY':True}
    builder=REPO/'td_builders/build_motion_preview.py'
    exec(compile(builder.read_text(encoding='utf-8'),str(builder),'exec'),namespace)
    comp=None

    def require(condition,name):
        if not condition:
            raise RuntimeError(name)
        result['checks'].append(name)

    try:
        namespace['build'](resolve,symbols,repo=REPO,name=TEST_NAME)
        comp=root.op(TEST_NAME)
        comp.par.Resolution=400
        comp.par.Usedat=True
        comp.appendCustomPage('Test').appendFloat('Testtime')[0].val=0
        comp.op('state_callbacks').text='''def onCook(scriptOp):
    scriptOp.copyNumpyArray(scriptOp.parent().op('motion_runtime').module.td_tick(
        scriptOp.parent(), now=scriptOp.parent().par.Testtime.eval()))
'''
        comp.unstore('motion_engine')
        poses=comp.op('poses')
        header=[cell.val for cell in poses.row(0)]

        def frame(t,source=(410,250,90),valid=1,extra=None,active=1):
            poses.clear()
            poses.appendRow(header)
            poses.appendRow(['test_a',*source,250,250,90,valid,active])
            if extra is not None:
                poses.appendRow(extra)
            comp.par.Testtime=t
            state=comp.op('state')
            state.cook(force=True)
            if state.errors():
                raise RuntimeError('state: '+str(state.errors()))
            return state.numpyArray(delayed=False).copy()

        def image(name):
            renderer=comp.op('render_'+name)
            renderer.cook(force=True)
            if renderer.errors():
                raise RuntimeError(name+': '+str(renderer.errors()))
            return renderer.numpyArray(delayed=False).copy()

        def green_pixels(array):
            return int(((array[:,:,1]>array[:,:,0]+.02)
                        &(array[:,:,1]>array[:,:,2]+.02)&(array[:,:,3]>.01)).sum())

        frame(0,source=(410,250,45))
        a=frame(4,source=(410,250,90))
        require(a[0,2,0]==1 and a[0,2,1]==0 and green_pixels(image('tabletop'))==0,
                'Vor Kontakt: voller Kreis, kein Grün trotz verbessertem Winkel')
        a=frame(4.02,source=(330,250,90))
        require(a[0,2,0]==1 and a[0,2,1]>0,
                'Erster geometrischer Kontakt: Grün startet, Kreis zunächst unverkleinert')
        a=frame(4.12,source=(310,250,90))
        require(0<a[0,2,0]<1 and a[0,2,2]>0,
                'Weitere Annäherung verkleinert Kreis und vergrößert Grün')
        size,opacity=float(a[0,2,2]),float(a[0,2,1])
        a=frame(4.14,source=(332,250,90))
        require(abs(float(a[0,2,2])-size)<1e-6 and abs(float(a[0,2,1])-opacity)<1e-6,
                'Kontaktverlust hält zuletzt erreichte grüne Formgröße')
        a=frame(4.25,source=(332,250,90))
        require(0<a[0,2,1]<opacity and green_pixels(image('tabletop'))>0,
                'Kontaktverlust: Grün bleibt im Shader während des Fades sichtbar')
        a=frame(4.38,source=(332,250,90))
        require(a[0,2,1]==0 and green_pixels(image('tabletop'))==0,
                'Kontaktverlust: Grün nach 220 ms vollständig ausgeblendet')
        a=frame(4.4,source=(330,250,90))
        require(a[0,2,0]==1 and a[0,2,2]==0,
                'Erneuter Kontakt beginnt ohne alten Fortschritt')
        a=frame(4.5,source=(250,250,96))
        require(a[0,2,0]>0 and a[0,2,3]==0,
                'Außerhalb Rotationstoleranz bleibt Navigationsradius positiv')
        a=frame(4.6,source=(250,250,90))
        surface=image('tabletop')
        center=surface[surface.shape[0]//2,surface.shape[1]//2]
        require(a[0,2,0]==0 and a[0,2,3]==1 and a[0,3,2]==0
                and center[1]>center[0]+.5 and center[3]>.99,
                'Ziel erreicht: Kreis null, grüne Platte und Dissolve sofort ohne Hold')
        a=frame(4.9,source=(270,250,105))
        require(a[0,2,0]==0 and a[0,2,3]==1 and abs(float(a[0,3,2])-.3)<1e-5,
                'Pose-Schwankung unterbricht oder wiederholt den Dissolve nicht')
        a=frame(5.61,source=(250,250,90))
        require(a[0,2,3]==2 and np.max(np.abs(image('tabletop')))<1e-6
                and np.max(np.abs(image('floor')))<1e-6,
                'Nach 1 s keine Restprojektion auf beiden Content-Ausgängen')
        a=frame(5.7,source=(250,250,90),
                extra=['test_b',100,100,0,100,400,0,1,1])
        require(a[0,2,3]==2 and a[1,2,3]==0 and image('floor')[:,:,3].max()>.9,
                'Abschluss von Tisch A entfernt die Navigation von Tisch B nicht')
        contact_baseline=comp.fetch('motion_engine',None).tables['test_a'].baseline
        a=frame(5.8,source=(269,250,90))
        require(a[0,2,3]==0 and a[0,2,0]>0,
                'Bewegung über 18 cm reaktiviert den abgeschlossenen Tisch')
        require(comp.fetch('motion_engine',None).tables['test_a'].baseline==contact_baseline
                and 0<a[0,2,0]<.5,
                'Reaktivierung bei fortbestehendem Kontakt erhält den Fortschritt')

        comp.par.Layoutrevision=int(comp.par.Layoutrevision.eval())+1
        frame(6)
        a=frame(8.51)
        radius=float(a[0,3,0])
        require(a[0,3,1]==1 and radius>0,'Idle-Puls startet nach 2 s Stillstand')
        a=frame(8.526,source=(410,249,90))
        require(abs(float(a[0,3,0])-radius)<1e-5 and a[0,3,1]==1,
                'Puls-Abbruch übernimmt den aktuellen Radius ohne Sprung')
        a=frame(8.616,source=(410,249,90))
        require(a[0,3,0]>radius and 0<a[0,3,1]<1,
                'Abgebrochener Puls wächst kontinuierlich und fadet weich aus')
        a=frame(8.716,source=(410,249,90))
        require(a[0,3,1]==0,'Puls-Abbruch nach 180 ms vollständig ausgeblendet')

        comp.par.Layoutrevision=int(comp.par.Layoutrevision.eval())+1
        frame(10,source=(450,250,90),active=0)
        frame(11.5,source=(450,250,90),active=0)
        require(image('tabletop')[:,:,3].max()>.9,
                'Globale Reveal-Welle erfasst auch einen inaktiven Tisch')

        comp.par.Layoutrevision=int(comp.par.Layoutrevision.eval())+1
        a=frame(12,source=(250,250,90),valid=0)
        engine=comp.fetch('motion_engine',None)
        require(engine.tables['test_a'].phase=='guidance' and a[0].max()==0,
                'Ungültige Pose kann keinen Erfolg auslösen')

        comp.par.Layoutrevision=int(comp.par.Layoutrevision.eval())+1
        frame(13,source=(330,250,90))
        frame(13.1,source=(250,250,90))
        a=frame(13.2,source=(410,250,90))
        state=comp.fetch('motion_engine',None).tables['test_a']
        require(a[0,2,3]==1 and state.baseline is None and not state.touching,
                'Kontaktverlust während Dissolve löscht nur die Kontakt-Baseline')
        frame(14.11,source=(410,250,90))
        a=frame(14.12,source=(330,250,90))
        b=frame(14.22,source=(310,250,90))
        require(a[0,2,3]==0 and a[0,2,0]==1 and 0<b[0,2,0]<1,
                'Nach Kontaktverlust startet erneute Annäherung mit frischem Fortschritt')

        # Probe the actual halo function independently of source/target clipping.
        # Only this temporary component changes; the live engine keeps running.
        pixel=comp.op('motion_pixel')
        if pixel.text.count('void main()') != 1 or 'float feedbackHalo(' not in pixel.text:
            raise RuntimeError('Aktualisierte Halo-Funktion fehlt im Prüfshader.')
        pixel.text=pixel.text.replace('void main()', 'void contentMain()',1)+'''
void main() {
    vec4 args=datum(0,0);
    vec2 offset=vec2(vUV.x,1.0-vUV.y)*500.0-250.0;
    fragColor=TDOutputSwizzle(white(feedbackHalo(offset,args.y,args.z,args.w,args.x)));
}
'''
        comp.op('state_callbacks').text='''def onCook(scriptOp):
    scriptOp.copyNumpyArray(scriptOp.parent().fetch('halo_probe_data'))
'''

        def halo(distance,angle):
            data=np.zeros((6,6,4),dtype=np.float32)
            data[0,0]=(distance,angle,.63,4)
            comp.store('halo_probe_data',data)
            comp.op('state').cook(force=True)
            return image('tabletop')[:,:,0]

        centered=halo(0,0)
        tolerance=1/255+1e-5  # Possible RGBA8 TOP quantization.
        require(centered.max()>.9
                and np.max(np.abs(centered-centered.T))<=tolerance
                and np.max(np.abs(centered-np.flip(centered,axis=0)))<=tolerance,
                'Grünes Feedback ist in der Zielmitte zentriert und symmetrisch')
        require(np.max(np.abs(centered-halo(7.99,71)))<=tolerance
                and np.max(np.abs(halo(2,0)-halo(2,180)))<=tolerance,
                'Richtungswechsel beim Mittelpunktdurchgang verändert die grüne Form nicht')
        require(np.max(np.abs(halo(7.99,71)-halo(8.01,71)))<=tolerance,
                'Übergang zur runden grünen Form ist an der Positionstoleranz stetig')
        result['passed']=True
    except Exception as error:
        result['failure']=str(error)
    finally:
        if comp is not None:
            comp.destroy()
            result['temporary_component_removed']=True
    result['check_count']=len(result['checks'])
    result['physical_validation']='not performed'
    return result


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    kinds=('containerCOMP','textDAT','tableDAT','scriptTOP','glslTOP','outTOP')
    print(json.dumps(check(symbol('op'),{name:symbol(name) for name in kinds}),
                     ensure_ascii=False,indent=2))
elif __name__=='__main__':
    raise RuntimeError('Im TD-Textport ausführen.')
