"""Textport: ursprüngliche Floor-Konturen aus der Reparatur-Rückfallkopie herstellen.

Keine neue Reparatur ausführen; kein Force-Cook, kein Speichern.
"""
import json
import runpy


def restore_original_floor_contours(resolve):
    helpers = runpy.run_path('/Users/Johannes/dev/Promotion_Prototypen/AISI/'
                             'td_builders/repair_aisi_joined_floor_contours.py',
                             init_globals={'_AISI_RESTORE_ONLY': True})
    return helpers['restore_joined_floor_contours'](resolve)


try:
    _td_resolve = op
except NameError:
    pass
else:
    print(json.dumps(restore_original_floor_contours(_td_resolve), indent=2))
    print('Ursprüngliche Floor-Konturen wiederhergestellt. Nichts gespeichert. '
          'OSC-Sender mit aktualisiertem Code neu starten und Discussion neu generieren.')
