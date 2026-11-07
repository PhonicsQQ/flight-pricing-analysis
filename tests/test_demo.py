"""Offline integration checks against locally collected artifacts, when present."""
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch
from flights.export_demo import export_payload
from flights.freeze import ROOT, FROZEN


@unittest.skipUnless((FROZEN/'manifest.json').exists(), 'Local research data not distributed')
class DemoExportTests(unittest.TestCase):
    def test_waiting_scenarios_agree_with_independent_python_pairs(self):
        import subprocess
        import shutil
        from statistics import median, mean
        if not shutil.which('node'):
            self.skipTest('Node only needed for development checks')
        payload=export_payload()
        code="""
        import fs from 'node:fs';import {waitingScenario} from './demo/core.mjs';
        const d=JSON.parse(fs.readFileSync(0,'utf8')),out=[];
        for(const route of ['ALL','ATL','MCO','DEN'])for(const lead of [60,45,30,21,14,7])for(const h of [1,3,7])
          out.push({route,lead,h,result:waitingScenario(d.trips.filter(t=>route==='ALL'||t.route===route),lead,h)});
        console.log(JSON.stringify(out));
        """
        p=subprocess.run(['node','--input-type=module','-e',code],input=json.dumps(payload),text=True,
                         capture_output=True,check=True,cwd=ROOT)
        for case in json.loads(p.stdout):
            changes=[]
            for trip in payload['trips']:
                if case['route']!='ALL' and trip['route']!=case['route']:
                    continue
                prices={point[2]:point[1] for point in trip['points']}
                a,b=case['lead'],case['lead']-case['h']
                if a in prices and b in prices:
                    changes.append(prices[b]-prices[a])
            result=case['result']
            if not changes:
                self.assertIsNone(result)
            else:
                self.assertEqual(result['trips'],len(changes))
                self.assertEqual(result['median'],median(changes))
                self.assertAlmostEqual(result['mean'],mean(changes))
                self.assertAlmostEqual(result['up'],sum(c>0 for c in changes)/len(changes))
                self.assertAlmostEqual(result['down'],sum(c<0 for c in changes)/len(changes))

    def test_export_needs_no_credentials_or_network_and_preserves_missing_trip(self):
        with patch.dict('os.environ', {}, clear=True), patch.object(socket, 'socket', side_effect=AssertionError('Network forbidden')):
            payload=export_payload()
        self.assertEqual(len(payload['trips']),168)
        self.assertEqual(sum(len(t['points']) for t in payload['trips']),10282)
        missing=[t for t in payload['trips'] if not t['points']]
        self.assertEqual([(t['route'],t['departure']) for t in missing],[('MCO','2026-12-21')])
        allowed={'id','route','departure','retrieved','holidays','points'}
        self.assertTrue(all(set(t)==allowed for t in payload['trips']))
        serialized=json.dumps(payload).lower()
        for forbidden in ['api_key','serpapi_api_key','account_quota','search_metadata','booking_token']:
            self.assertNotIn(forbidden,serialized)

    def test_browser_summaries_match_saved_python_results(self):
        import subprocess
        import shutil
        if not shutil.which('node'):
            self.skipTest('Node only needed for development checks')
        code="""
        import fs from 'node:fs';
        import {summarize} from './demo/core.mjs';
        const d=JSON.parse(fs.readFileSync(0,'utf8'));
        console.log(JSON.stringify([1,3,7].map(h=>summarize(d.trips,h))));
        """
        payload=export_payload()
        p=subprocess.run(['node','--input-type=module','-e',code],input=json.dumps(payload),text=True,
                         capture_output=True,check=True,cwd=ROOT)
        for js,py in zip(json.loads(p.stdout),payload['results']['overall']):
            self.assertEqual(js['pairs'],py['pairs'])
            self.assertEqual(js['trips'],py['trips'])
            self.assertAlmostEqual(js['usd'],py['mean_usd'])
            self.assertAlmostEqual(js['pct'],py['mean_pct'])
            self.assertAlmostEqual(js['up'],py['trip_up'])
