"""Discussion-Sitzfläche mit drei Chairs für die visuelle Größenentscheidung."""
from pathlib import Path
import argparse
import json
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

from aisi.core.models import TableState, TableTarget
from aisi.core.table_geometry import (
    circle_inside_convex_polygon, resolve_table_state_geometry,
    table_world_footprint, _convex_point_and_edge_distance,
)
from aisi.analysis.rect_groupwork_adaptive_prototype import single_long_side_clearance_region
from aisi.generation.layout_synthesizer import DISCUSSION_SEAT_CLEARANCE_DEPTH_CM


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    table=TableState('table_0',0.,0.,0.,160.,80.,table_type='rect')
    target=TableTarget(table.table_id,0.,0.,target_rot_deg=0.)
    geometry=resolve_table_state_geometry(table)
    depth=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM
    region=single_long_side_clearance_region(target,table,seat_direction=(0.,1.),clearance_depth_cm=depth)
    y=geometry.nominal_depth/2+depth/2
    centers=[(-52.,y),(0.,y),(52.,y)]
    footprint=table_world_footprint(table,(0.,0.),0.)
    fig,axes=plt.subplots(1,2,figsize=(13.5,6.8))
    records=[]
    for ax,radius in zip(axes,(25.,22.5)):
        valid=all(circle_inside_convex_polygon(c,radius,region) for c in centers)
        margin=min(_convex_point_and_edge_distance(c,region)[1]-radius for c in centers)
        records.append(dict(diameter_cm=2*radius,centers_cm=centers,
                            fully_inside=valid,min_seat_boundary_margin_cm=margin,
                            own_table_gap_cm=depth/2-radius,adjacent_chair_gap_cm=52-2*radius))
        def draw(panel,labels=False):
            panel.add_patch(Polygon(region,facecolor='#dcecf3',edgecolor='#277595',lw=1.5))
            panel.add_patch(Polygon(footprint,facecolor='#b9c1c9',edgecolor='#475569',lw=1.5))
            for i,center in enumerate(centers):
                panel.add_patch(Circle(center,radius,facecolor='#f3c383',edgecolor='#b76516',lw=1.8,alpha=.8))
                arc=[(center[0]+radius*math.cos(math.tau*k/720),center[1]+radius*math.sin(math.tau*k/720)) for k in range(721)]
                for a,b in zip(arc,arc[1:]):
                    if not circle_inside_convex_polygon(((a[0]+b[0])/2,(a[1]+b[1])/2),0.,region):
                        panel.plot((a[0],b[0]),(a[1],b[1]),color='#cc2836',lw=3)
                if labels:panel.text(*center,str(i+1),ha='center',va='center',fontsize=11)
        draw(ax,True)
        ax.text(0,103,'Äußere Sitz-/Bewegungsfläche',ha='center',color='#205f78',fontsize=10)
        ax.text(0,12,'Rect-Tisch · 160 × 80 cm',ha='center',fontsize=11)
        ax.annotate('Zum Ringzentrum',xy=(0,-28),xytext=(0,-4),ha='center',fontsize=9,
                    arrowprops=dict(arrowstyle='->',color='#334155'),color='#334155')
        ax.annotate('',xy=(-80,-49),xytext=(80,-49),arrowprops=dict(arrowstyle='<->',color='#475569'))
        ax.text(0,-54,'160 cm',ha='center',va='top',fontsize=9)
        ax.annotate('',xy=(-94,40),xytext=(-94,90),arrowprops=dict(arrowstyle='<->',color='#277595'))
        ax.text(-99,65,'50 cm',ha='center',va='center',rotation=90,fontsize=9,color='#205f78')
        ax.set(xlim=(-112,112),ylim=(-65,118),aspect='equal',xlabel='X [cm]',ylabel='Y [cm]')
        ax.set_title(f"Chair Ø {2*radius:g} cm\n"+('vollständig in der Sitzfläche' if valid else 'äußere Chairs überschreiten die Rundung'),fontsize=12,pad=12)
        inset=ax.inset_axes([.7,.02,.27,.23])
        draw(inset)
        inset.set(xlim=(57,66),ylim=(84,93),aspect='equal',xticks=[],yticks=[])
        inset.set_title('Ecke vergrößert',fontsize=8)
        note=(f'Überstand an der Rundung: {max(0,-margin):.2f} cm' if not valid else f'Mindestreserve in der Sitzfläche: {margin:.2f} cm')
        ax.text(.02,.03,note+'\n'+f'Zwischen den Chairs: {52-2*radius:g} cm',transform=ax.transAxes,fontsize=8,va='bottom',color='#a6202b' if not valid else '#236442')
    fig.suptitle('Discussion · ein Tisch mit drei Chairs auf der Außenseite',fontsize=15,y=.98)
    fig.tight_layout(rect=(0,0,1,.94))
    for suffix in ('png','svg','pdf'):fig.savefig(args.output/f'discussion_drei_chairs.{suffix}',dpi=170)
    plt.close(fig)
    assert records[0]['fully_inside'] is False and records[1]['fully_inside'] is True
    assert all(r['adjacent_chair_gap_cm']>0 for r in records)
    (args.output/'fit.json').write_text(json.dumps(dict(seat_depth_cm=depth,corner_radius_cm=30.,
        comparison=records,runtime_changed=False),ensure_ascii=False,indent=2)+'\n')
    print(args.output/'discussion_drei_chairs.png')


if __name__=='__main__':main()
