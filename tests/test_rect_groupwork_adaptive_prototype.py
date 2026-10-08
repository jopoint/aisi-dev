from __future__ import annotations

import math
import itertools
from pathlib import Path
import unittest
from unittest.mock import patch

from aisi.analysis.rect_groupwork_adaptive_prototype import (
    SEAT_CLEARANCE_DEPTH_CM,
    _all_group_clearance_regions_inside_roi,
    _group_clearance_regions,
    _satisfies_prototype_hard_constraints,
    _compatible_option_combinations, _group_options, _fit_option_to_roi,
    _select_local_options, _materialize_candidate, _source_movement_candidate_key,
    _polygons_overlap_with_positive_area,
    _rounded_outer_singleton_strip,
    enumerate_pair_partitions,
    solve_rect_groupwork_prototype,
)
from aisi.core.models import ROI, SceneState, TableState, TargetStructure
from aisi.core.table_geometry import table_world_footprint
from aisi.generation.layout_synthesizer import synthesize_layout
from aisi.input.scene_loader import build_scene_state_from_json


SCENE_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "data" / "aisi" / "scenes" / "rect_groupwork_validation"
)


def _scene(count: int) -> SceneState:
    return build_scene_state_from_json(
        SCENE_DIRECTORY / f"rect_groupwork_{count}.json", learning_format="groupwork"
    )


def _rotate(point: tuple[float, float], angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    x, y = point[0] - 250.0, point[1] - 250.0
    return (
        250.0 + x * math.cos(angle) - y * math.sin(angle),
        250.0 + x * math.sin(angle) + y * math.cos(angle),
    )


def _legacy_id_template_distances(scene: SceneState) -> list[float]:
    """Return movement from the rejected fixed, ID-bound Groupwork slots."""
    centers = {
        2: ((250.0, 250.0),),
        3: ((150.0, 250.0), (350.0, 250.0)),
        4: ((150.0, 250.0), (350.0, 250.0)),
        5: ((120.0, 160.0), (380.0, 160.0), (250.0, 360.0)),
    }[len(scene.tables)]
    slots: list[tuple[float, float]] = []
    ordered = sorted(scene.tables, key=lambda table: table.table_id)
    for index, center in enumerate(centers):
        if index * 2 + 1 < len(ordered):
            slots.extend(((center[0], center[1] - 42.0), (center[0], center[1] + 42.0)))
        else:
            slots.append(center)
    return [
        math.dist((table.x, table.y), slot)
        for table, slot in zip(ordered, slots)
    ]


class RectGroupworkAdaptivePrototypeTests(unittest.TestCase):
    def test_local_strip_cache_includes_dimensions_direction_and_effective_radius(self):
        strip=_rounded_outer_singleton_strip
        original=strip(160.,60.,outer_direction=1.)
        self.assertIs(strip(160.,60.,outer_direction=1.),original)
        self.assertNotEqual(strip(170.,60.,outer_direction=1.),original)
        self.assertNotEqual(strip(160.,60.,outer_direction=-1.),original)
        with patch('aisi.analysis.rect_groupwork_adaptive_prototype.SINGLETON_OUTER_CORNER_RADIUS_CM',12.):
            self.assertNotEqual(strip(160.,60.,outer_direction=1.),original)
        self.assertEqual(strip(160.,60.,outer_direction=1.),original)

    def test_polygon_fast_path_matches_full_sat_at_contacts_and_rotations(self):
        overlap=_polygons_overlap_with_positive_area
        first=table_world_footprint(TableState('a',0,0,0,160,80,table_type='rect'),(0,0),0)
        pairs=[(first,table_world_footprint(TableState('b',x,y,angle,160,80,table_type='rect'),(x,y),angle))
               for angle in (0,17,37,90,175)
               for x,y in ((0,0),(160,0),(160-1e-6,0),(160+1e-6,0),
                           (160-1e-9,0),(160+1e-9,0),(0,80),(0,80+1e-9),(350,300))]
        state=_scene(2);group=tuple(state.tables)
        option=_fit_option_to_roi(state,_group_options(group,pair_index=0,refined=False)[0])
        curved=_group_clearance_regions(state,option.targets,(tuple(t.table_id for t in group),))[0][1][0]
        pairs.extend((first,tuple((x+shift,y) for x,y in curved)) for shift in (-500,0,500))
        # Force the old SAT path independently of bounding boxes.
        overlap.cache_clear()
        with patch('aisi.analysis.rect_groupwork_adaptive_prototype.footprint_bounds',
                   return_value=(-math.inf,-math.inf,math.inf,math.inf)):
            expected=[overlap(a,b) for a,b in pairs]
        overlap.cache_clear()
        self.assertEqual([overlap(a,b) for a,b in pairs],expected)
        a,b=pairs[-1];before=overlap.cache_info().hits
        self.assertEqual(overlap(a,b),expected[-1])
        self.assertGreater(overlap.cache_info().hits,before)
        # A changed polygon must not reuse a formerly negative entry.
        self.assertFalse(overlap(first,tuple((x+1000,y) for x,y in first)))
        self.assertTrue(overlap(first,first))

    def test_early_compatibility_preserves_all_canonical_candidates_and_order(self):
        geometry_cache={};compatibility_cache={};valid_count=0;invalid_count=0
        for count in (2,3,4,5):
            state=_scene(count)
            # Each solve owns its caches; sources and ROI cannot leak between runs.
            geometry_cache.clear();compatibility_cache.clear()
            for partition in enumerate_pair_partitions(state.tables)[:3]:
                options=[_select_local_options(state,tuple(_fit_option_to_roi(state,o)
                    for o in _group_options(group,pair_index=i,refined=True)),limit=4)
                    for i,group in enumerate(partition)]
                reference=[c for choice in itertools.product(*options)
                    if (c:=_materialize_candidate(state,partition,choice,True)) is not None]
                actual=[_materialize_candidate(state,partition,choice,True)
                    for choice in _compatible_option_combinations(state,options,geometry_cache,compatibility_cache)]
                self.assertEqual(actual,reference)
                valid_count+=len(reference)
                invalid_count+=math.prod(map(len,options))-len(reference)
        self.assertGreater(valid_count,0)
        self.assertGreater(invalid_count,0)

    def test_filtered_source_search_keeps_exhaustive_best_including_rejections(self):
        state=_scene(3);candidates=[]
        def collect(candidate):
            candidates.append(candidate)
            return False
        with self.assertRaises(ValueError):
            solve_rect_groupwork_prototype(state,selection='source_movement',candidate_filter=collect)
        # Reject the unconstrained optimum, as Chair checks may do, and verify
        # that pruning starts only after an accepted incumbent exists.
        minimum=min(c.objective.max_displacement_cm for c in candidates)
        eligible=lambda c:c.objective.max_displacement_cm>minimum+1.
        expected=min((c for c in candidates if eligible(c)),key=_source_movement_candidate_key)
        calls=[]
        def accept(candidate):
            calls.append(candidate)
            return eligible(candidate)
        actual=solve_rect_groupwork_prototype(state,selection='source_movement',candidate_filter=accept)
        self.assertEqual(actual,expected)
        self.assertLess(len(calls),len(candidates))

    def test_enumerates_every_pair_singleton_partition(self) -> None:
        tables = [TableState(f"table_{index}", 100.0 + index * 20.0, 250.0) for index in range(5)]
        partitions = enumerate_pair_partitions(tables)
        self.assertEqual(len(partitions), 15)
        self.assertTrue(all(sorted(map(len, partition)) == [1, 2, 2] for partition in partitions))

    def test_rotation_equivariance_away_from_roi_boundaries(self) -> None:
        base_tables = [
            TableState("alpha", 205.0, 250.0, 0.0, 160.0, 80.0, table_type="rect"),
            TableState("beta", 295.0, 250.0, 0.0, 160.0, 80.0, table_type="rect"),
        ]
        angle = 37.0
        rotated_tables = [
            TableState(
                table.table_id,
                *_rotate((table.x, table.y), angle),
                table.rot_deg + angle,
                table.width,
                table.height,
                table_type="rect",
            )
            for table in base_tables
        ]
        base = solve_rect_groupwork_prototype(SceneState(ROI(0.0, 0.0, 500.0, 500.0), base_tables, "groupwork"))
        rotated = solve_rect_groupwork_prototype(SceneState(ROI(0.0, 0.0, 500.0, 500.0), rotated_tables, "groupwork"))
        rotated_by_id = {target.table_id: target for target in rotated.table_targets}
        for target in base.table_targets:
            expected_x, expected_y = _rotate((target.target_x, target.target_y), angle)
            actual = rotated_by_id[target.table_id]
            self.assertAlmostEqual(actual.target_x, expected_x, places=6)
            self.assertAlmostEqual(actual.target_y, expected_y, places=6)
            self.assertAlmostEqual(actual.target_rot_deg, target.target_rot_deg + angle, places=6)

    def test_translation_equivariance_away_from_roi_boundaries(self) -> None:
        base_tables = [
            TableState("alpha", 205.0, 250.0, 0.0, 160.0, 80.0, table_type="rect"),
            TableState("beta", 295.0, 250.0, 0.0, 160.0, 80.0, table_type="rect"),
        ]
        translated_tables = [
            TableState(table.table_id, table.x + 5.0, table.y - 5.0, table.rot_deg, table.width, table.height, table_type="rect")
            for table in base_tables
        ]
        base = solve_rect_groupwork_prototype(SceneState(ROI(0.0, 0.0, 500.0, 500.0), base_tables, "groupwork"))
        translated = solve_rect_groupwork_prototype(SceneState(ROI(0.0, 0.0, 500.0, 500.0), translated_tables, "groupwork"))
        translated_by_id = {target.table_id: target for target in translated.table_targets}
        for target in base.table_targets:
            actual = translated_by_id[target.table_id]
            self.assertAlmostEqual(actual.target_x, target.target_x + 5.0, places=6)
            self.assertAlmostEqual(actual.target_y, target.target_y - 5.0, places=6)

    def test_geometry_is_independent_of_table_id_sorting(self) -> None:
        source = _scene(4)
        renamed = SceneState(
            source.roi,
            [
                TableState(
                    f"renamed_{index}", table.x, table.y, table.rot_deg, table.width, table.height, table_type="rect"
                )
                for index, table in enumerate(reversed(source.tables))
            ],
            "groupwork",
        )
        original = solve_rect_groupwork_prototype(source)
        variant = solve_rect_groupwork_prototype(renamed)
        original_geometry = sorted(
            (round(target.target_x, 6), round(target.target_y, 6), round(target.target_rot_deg, 6))
            for target in original.table_targets
        )
        variant_geometry = sorted(
            (round(target.target_x, 6), round(target.target_y, 6), round(target.target_rot_deg, 6))
            for target in variant.table_targets
        )
        self.assertEqual(variant_geometry, original_geometry)

    def test_regression_scenes_are_better_than_id_bound_template_reference(self) -> None:
        for count in range(2, 6):
            with self.subTest(count=count):
                scene = _scene(count)
                adaptive = solve_rect_groupwork_prototype(scene)
                reference_distances = _legacy_id_template_distances(scene)
                self.assertLess(adaptive.objective.max_displacement_cm, max(reference_distances))
                self.assertLess(adaptive.objective.total_displacement_cm, sum(reference_distances))
                self.assertEqual(adaptive.objective.crossing_count, 0)

    def test_is_deterministic_and_satisfies_full_hard_constraints(self) -> None:
        scene = _scene(5)
        first = solve_rect_groupwork_prototype(scene)
        second = solve_rect_groupwork_prototype(scene)
        self.assertEqual(first, second)
        self.assertTrue(
            _satisfies_prototype_hard_constraints(
                scene,
                first.table_targets,
                first.groups,
                first.generation_notes,
            )
        )
        self.assertTrue(_all_group_clearance_regions_inside_roi(scene, first.table_targets, first.groups))

    def test_singleton_has_two_full_width_60_cm_long_side_strips(self) -> None:
        scene = _scene(3)
        result = solve_rect_groupwork_prototype(scene)
        regions = _group_clearance_regions(scene, result.table_targets, result.groups)
        singleton_group, singleton_regions = next(item for item in regions if len(item[0]) == 1)
        self.assertEqual(len(singleton_group), 1)
        self.assertEqual(len(singleton_regions), 2)
        for strip in singleton_regions:
            self.assertEqual(len(strip), 20)
            self.assertAlmostEqual(math.dist(strip[0], strip[1]), 160.0, places=6)
            self.assertGreater(
                len({round(math.dist(first, second), 6) for first, second in zip(strip, strip[1:] + strip[:1])}),
                2,
            )
        self.assertTrue(_all_group_clearance_regions_inside_roi(scene, result.table_targets, result.groups))

    def test_pair_clearance_is_a_curved_ellipse(self) -> None:
        scene = _scene(3)
        result = solve_rect_groupwork_prototype(scene)
        regions = _group_clearance_regions(scene, result.table_targets, result.groups)
        _, pair_regions = next(item for item in regions if len(item[0]) == 2)
        self.assertEqual(len(pair_regions), 1)
        self.assertEqual(len(pair_regions[0]), 48)

    def test_pair_rotation_strongly_prefers_axial_source_mean(self) -> None:
        scene = SceneState(
            ROI(0.0, 0.0, 500.0, 500.0),
            [
                TableState("left", 180.0, 220.0, 90.0, 160.0, 80.0, table_type="rect"),
                TableState("right", 320.0, 220.0, 90.0, 160.0, 80.0, table_type="rect"),
            ],
            "groupwork",
        )
        result = solve_rect_groupwork_prototype(scene, selection="clearance")
        self.assertAlmostEqual(result.objective.pair_orientation_deviation_deg, 0.0, places=6)
        self.assertTrue(
            all(abs(abs(target.target_rot_deg) - 90.0) < 1e-6 for target in result.table_targets)
        )

    def test_rotation_preference_keeps_available_zero_overlap_partition(self) -> None:
        scene = SceneState(
            ROI(0.0, 0.0, 500.0, 500.0),
            [
                TableState("table_0", 139.286, 267.143, 0.0, 160.0, 80.0, table_type="rect"),
                TableState("table_1", 393.571, 147.143, 0.0, 160.0, 80.0, table_type="rect"),
                TableState("table_2", 394.286, 336.429, 10.0, 160.0, 80.0, table_type="rect"),
                TableState("table_3", 141.429, 136.429, 90.0, 160.0, 80.0, table_type="rect"),
                TableState("table_5", 190.714, 430.0, 0.0, 160.0, 80.0, table_type="rect"),
            ],
            "groupwork",
        )
        result = solve_rect_groupwork_prototype(scene, selection="clearance")
        self.assertAlmostEqual(result.objective.clearance_overlap_area_cm2, 0.0, places=5)
        self.assertAlmostEqual(result.objective.pair_orientation_deviation_deg, 0.0, places=5)

    def test_spread_profile_improves_island_gap_within_its_explicit_movement_budget(self) -> None:
        scene = _scene(5)
        movement = solve_rect_groupwork_prototype(scene)
        spread = solve_rect_groupwork_prototype(
            scene, selection="spread", movement_budget_cm=50.0
        )
        self.assertLessEqual(
            spread.objective.clearance_overlap_area_cm2,
            movement.objective.clearance_overlap_area_cm2 + 1e-6,
        )
        self.assertLessEqual(
            spread.objective.max_displacement_cm,
            movement.objective.max_displacement_cm + 50.0,
        )

    def test_aggressive_clearance_profile_removes_count_five_zone_overlap(self) -> None:
        scene = _scene(5)
        result = solve_rect_groupwork_prototype(scene, selection="clearance")
        self.assertAlmostEqual(result.objective.clearance_overlap_area_cm2, 0.0, places=5)

    def test_production_rect_groupwork_uses_the_approved_adaptive_solution(self) -> None:
        for count in range(2, 6):
            with self.subTest(count=count):
                scene = _scene(count)
                expected = solve_rect_groupwork_prototype(scene, selection="clearance")
                proposal = synthesize_layout(
                    scene,
                    scene_features=None,
                    target_profile=None,
                    target_structure=TargetStructure(structure_type="cluster_zones"),
                    transformation_strength=1.0,
                )
                self.assertEqual(
                    [
                        (
                            target.table_id,
                            round(target.target_x, 6),
                            round(target.target_y, 6),
                            round(target.target_rot_deg, 6),
                        )
                        for target in proposal.table_targets
                    ],
                    [
                        (
                            target.table_id,
                            round(target.target_x, 6),
                            round(target.target_y, 6),
                            round(target.target_rot_deg, 6),
                        )
                        for target in expected.table_targets
                    ],
                )
                self.assertIn("rect_groupwork=adaptive_local_clearance", proposal.generation_notes)
                self.assertFalse(
                    any(
                        note.startswith("final_clearance_violations=")
                        for note in proposal.generation_notes
                    )
                )
                self.assertTrue(
                    _satisfies_prototype_hard_constraints(
                        scene,
                        tuple(proposal.table_targets),
                        expected.groups,
                        tuple(proposal.generation_notes),
                    )
                )
