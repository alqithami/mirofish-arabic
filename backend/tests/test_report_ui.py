import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'app' / 'services' / 'report_ui.py'


def load_report_ui_module():
    flask_stub = types.ModuleType('flask')
    flask_stub.request = None
    sys.modules.setdefault('flask', flask_stub)

    app_pkg = sys.modules.setdefault('app', types.ModuleType('app'))
    app_pkg.__path__ = [str(ROOT / 'app')]

    services_pkg = sys.modules.setdefault('app.services', types.ModuleType('app.services'))
    services_pkg.__path__ = [str(ROOT / 'app' / 'services')]

    utils_pkg = sys.modules.setdefault('app.utils', types.ModuleType('app.utils'))
    utils_pkg.__path__ = [str(ROOT / 'app' / 'utils')]

    locale_stub = types.ModuleType('app.utils.locale')
    locale_stub.normalize_locale = lambda candidate, default='en': (candidate or default).split(',')[0].split(';')[0].strip().lower().split('-')[0] if candidate else default
    sys.modules['app.utils.locale'] = locale_stub

    zep_stub = types.ModuleType('app.services.zep_tools')
    for name in ['SearchResult', 'InsightForgeResult', 'PanoramaResult', 'InterviewResult']:
        setattr(zep_stub, name, type(name, (), {}))
    sys.modules['app.services.zep_tools'] = zep_stub

    spec = importlib.util.spec_from_file_location('app.services.report_ui', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules['app.services.report_ui'] = module
    spec.loader.exec_module(module)
    return module


report_ui = load_report_ui_module()


class ReportUiTests(unittest.TestCase):
    def test_extract_final_answer_multilingual(self):
        self.assertEqual(report_ui.extract_final_answer('Final Answer: Hello world'), 'Hello world')
        self.assertEqual(report_ui.extract_final_answer('الإجابة النهائية: مرحبا بالعالم'), 'مرحبا بالعالم')
        self.assertEqual(report_ui.extract_final_answer('最终答案：你好世界'), '你好世界')
        self.assertTrue(report_ui.has_final_answer_marker('النتيجة النهائية: نص'))

    def test_section_payload_has_new_metrics(self):
        payload = report_ui.build_section_ui_payload(
            title='Signals',
            content='## Signals\n\n- Alpha link [source](https://example.com)\n- Beta\n\n> Quote block',
            section_index=1,
            locale='en',
        )
        self.assertGreaterEqual(payload['citationCount'], 1)
        self.assertGreaterEqual(payload['factLikeCount'], 2)
        self.assertGreaterEqual(payload['calloutCount'], 1)
        self.assertGreaterEqual(payload['sentenceCount'], 1)

    def test_llm_payload_has_structured_response_metrics(self):
        payload = report_ui.build_llm_response_ui_payload(
            '''Final Answer:
## Outlook

- First evidence point [ref](https://example.com)
- Second point

> Quoted concern''',
            locale='en',
            has_final_answer=True,
        )
        self.assertTrue(payload['hasFinalAnswer'])
        self.assertGreaterEqual(payload['citationCount'], 1)
        self.assertGreaterEqual(payload['factLikeCount'], 2)
        self.assertGreaterEqual(payload['quoteCount'], 1)
        self.assertIn('Outlook', payload['headings'])
        self.assertTrue(payload['summaryBullets'])
        self.assertTrue(payload['factCards'])
        self.assertTrue(payload['citationCards'])
        self.assertTrue(payload['quoteCards'])

    def test_llm_payload_builds_claim_cards_against_evidence_context(self):
        payload = report_ui.build_llm_response_ui_payload(
            '''Final Answer:
- Student organizers are likely to escalate pressure on the administration.
- Public sympathy is widening across online communities.''',
            locale='en',
            has_final_answer=True,
            evidence_context={
                'kind': 'section_source_bundle',
                'factCards': [
                    {'text': 'Student organizers coordinated a boycott and threatened escalation.', 'preview': 'Students coordinated a boycott.', 'sourceTool': 'insight_forge'},
                    {'text': 'Online communities on Reddit expressed broader sympathy.', 'preview': 'Reddit sympathy is growing.', 'sourceTool': 'interview_agents'},
                ],
                'quoteCards': [
                    {'text': 'We finally have leverage.', 'preview': 'We finally have leverage.', 'sourceTool': 'interview_agents'}
                ],
                'citationCards': [
                    {'label': 'Campus source', 'url': 'https://example.com/source', 'sourceTool': 'insight_forge'}
                ],
                'toolsUsed': ['insight_forge', 'interview_agents'],
                'queries': ['campus reaction'],
            },
        )

        self.assertTrue(payload['claimBundle']['claimCount'] >= 2)
        self.assertTrue(payload['claimCards'])
        self.assertTrue(any(card['hasEvidence'] for card in payload['claimCards']))
        self.assertIn('supportingFacts', payload['claimCards'][0])

    def test_section_payload_builds_claim_cards_from_source_bundle(self):
        source_bundle = {
            'kind': 'section_source_bundle',
            'factCards': [{'text': 'Agents expect a stronger boycott wave next week.', 'preview': 'Boycott wave expected.', 'sourceTool': 'interview_agents'}],
            'citationCards': [{'label': 'Interview note', 'url': 'https://example.com/interview', 'sourceTool': 'interview_agents'}],
            'toolsUsed': ['interview_agents'],
            'queries': ['boycott escalation'],
        }
        payload = report_ui.build_section_ui_payload(
            title='Signals',
            content='## Signals\n\n- The boycott wave is likely to intensify next week.',
            section_index=1,
            locale='en',
            source_bundle=source_bundle,
        )
        self.assertTrue(payload['claimCards'])
        self.assertEqual(payload['claimBundle']['toolsUsed'], ['interview_agents'])
        self.assertTrue(payload['claimCards'][0]['citationCount'] >= 1)

    def test_interview_payload_has_summary_counts(self):
        payload = report_ui.normalize_interview_result_for_ui({
            'interview_topic': 'Topic',
            'summary': 'Summary text',
            'interviews': [{
                'agent_name': 'A',
                'agent_role': 'Analyst',
                'response': 'Twitter: Strong support\n\nReddit: Mixed reaction',
                'questions': ['Q1', 'Q2'],
                'key_quotes': ['Quote 1']
            }]
        }, locale='en')
        self.assertEqual(payload['quoteCount'], 1)
        self.assertEqual(payload['questionCount'], 2)
        self.assertIn('twitter', payload['platforms'])
        self.assertIn('reddit', payload['platforms'])
        self.assertTrue(payload['summaryBullets'])
        self.assertTrue(payload['interviewCards'])
        self.assertEqual(payload['interviews'][0]['qaPairs'][0]['question'], 'Q1')

    def test_interview_payload_splits_answers_into_qa_pairs(self):
        payload = report_ui.normalize_interview_result_for_ui({
            'interview_topic': 'Topic',
            'interview_questions': ['Q1', 'Q2'],
            'interviews': [{
                'agent_name': 'B',
                'response': 'Twitter response:\nQuestion 1: First answer\n\nQuestion 2: Second answer\n\nReddit response:\nQuestion 1: Alt first\n\nQuestion 2: Alt second'
            }]
        }, locale='en')
        qa_pairs = payload['interviews'][0]['qaPairs']
        self.assertEqual(len(qa_pairs), 2)
        self.assertEqual(qa_pairs[0]['twitterAnswer'], 'First answer')
        self.assertEqual(qa_pairs[1]['redditAnswer'], 'Alt second')
        self.assertTrue(qa_pairs[0]['isDualPlatform'])

    def test_normalize_section_entry_backfills_new_ui_fields(self):
        entry = report_ui.normalize_section_entry_for_ui({
            'section_index': 1,
            'title': 'Signals',
            'content': '## Signals\n\n- Alpha [ref](https://example.com)\n> Quote line',
            'ui_payload': {'kind': 'section', 'version': 1, 'preview': 'Old preview'}
        }, locale='en')
        self.assertEqual(entry['ui_payload']['preview'], 'Old preview')
        self.assertTrue(entry['ui_payload']['factCards'])
        self.assertTrue(entry['ui_payload']['citationCards'])
        self.assertTrue(entry['ui_payload']['quoteCards'])

    def test_section_source_bundle_aggregates_structured_tool_payloads(self):
        bundle = report_ui.build_section_source_bundle([
            {
                'toolName': 'insight_forge',
                'iteration': 1,
                'parameters': {'query': 'Campus reaction'},
                'payload': {
                    'kind': 'insight_forge',
                    'query': 'Campus reaction',
                    'summary': 'Signals point to a rapid escalation.',
                    'factCards': [{'text': 'Students coordinated a boycott.'}],
                    'citationCards': [{'label': 'Source', 'url': 'https://example.com'}],
                    'entityCards': [{'name': 'Student Union', 'type': 'Organization', 'preview': 'Key organizer'}],
                    'relationCards': [{'source': 'Students', 'relation': 'pressure', 'target': 'Administration'}],
                    'stats': {'facts': 7, 'entities': 3, 'relationships': 2},
                },
            },
            {
                'toolName': 'interview_agents',
                'iteration': 2,
                'parameters': {'interview_topic': 'Public reaction'},
                'payload': {
                    'kind': 'interview_agents',
                    'topic': 'Public reaction',
                    'summary': 'Agents report rising public sympathy.',
                    'platforms': ['twitter', 'reddit'],
                    'questionCount': 2,
                    'quoteCount': 1,
                    'interviewCards': [{'name': 'Agent A', 'role': 'Student', 'preview': 'Support is growing quickly.'}],
                    'interviews': [{
                        'questions': ['Why now?'],
                        'qaPairs': [{'question': 'Why now?', 'twitterAnswer': 'Momentum is building.', 'redditAnswer': 'Momentum is building.', 'platforms': ['twitter', 'reddit']}],
                        'quoteCards': [{'text': 'We finally have leverage.'}],
                    }],
                },
            },
        ], locale='en')

        self.assertEqual(bundle['counts']['toolResults'], 2)
        self.assertIn('Campus reaction', bundle['queries'])
        self.assertIn('twitter', bundle['platforms'])
        self.assertTrue(bundle['factCards'])
        self.assertTrue(bundle['citationCards'])
        self.assertTrue(bundle['entityCards'])
        self.assertTrue(bundle['relationCards'])
        self.assertTrue(bundle['interviewCards'])
        self.assertTrue(bundle['questionCards'])
        self.assertTrue(bundle['quoteCards'])
        self.assertTrue(bundle['toolRuns'][0]['runId'])
        self.assertTrue(bundle['factCards'][0]['evidenceId'])
        self.assertTrue(bundle['evidenceIndex'])
        self.assertGreaterEqual(bundle['counts']['evidenceItems'], 1)

    def test_normalize_section_entry_carries_source_bundle_into_ui_payload(self):
        entry = report_ui.normalize_section_entry_for_ui({
            'section_index': 2,
            'title': 'Research',
            'content': '## Research\n\n- Point one',
            'source_bundle': {
                'kind': 'section_source_bundle',
                'version': 1,
                'queries': ['What are the strongest signals?'],
                'counts': {'toolResults': 1, 'facts': 2},
                'factCards': [{'text': 'Signal A', 'preview': 'Signal A'}],
            },
        }, locale='en')

        self.assertIn('sourceBundle', entry['ui_payload'])
        self.assertEqual(entry['ui_payload']['sourceBundle']['queries'][0], 'What are the strongest signals?')
        self.assertTrue(entry['ui_payload']['sourceBundle']['factCards'])

    def test_normalize_log_entry_uses_evidence_context_for_claim_cards(self):
        entry = report_ui.normalize_log_entry_for_ui({
            'action': 'llm_response',
            'details': {
                'response': 'Final Answer:\n- Student groups are likely to intensify their campaign.',
                'has_final_answer': True,
                'evidence_context': {
                    'factCards': [{'text': 'Student groups are preparing a larger campaign.', 'preview': 'Larger campaign incoming.', 'sourceTool': 'insight_forge'}],
                    'citationCards': [{'label': 'Primary source', 'url': 'https://example.com', 'sourceTool': 'insight_forge'}],
                    'toolsUsed': ['insight_forge'],
                },
            }
        }, locale='en')

        payload = entry['details']['ui_payload']
        self.assertTrue(payload['claimCards'])
        self.assertTrue(payload['claimCards'][0]['hasEvidence'])

    def test_build_report_state_payload_rolls_up_claim_metrics(self):
        payload = report_ui.build_report_state_payload(
            report={'report_id': 'r1', 'status': 'completed'},
            outline={'sections': [{'title': 'Signals'}]},
            sections=[{
                'section_index': 1,
                'title': 'Signals',
                'status': 'completed',
                'content': '## Signals\n\n- Pressure is rising.',
                'source_bundle': {
                    'kind': 'section_source_bundle',
                    'factCards': [{'text': 'Pressure is rising on campus.', 'preview': 'Pressure is rising.', 'sourceTool': 'insight_forge'}],
                    'citationCards': [{'label': 'Source', 'url': 'https://example.com', 'sourceTool': 'insight_forge'}],
                    'toolsUsed': ['insight_forge'],
                },
            }],
            progress={'status': 'completed'},
            locale='en',
        )

        totals = payload['summary']['evidenceTotals']
        self.assertGreaterEqual(totals['claims'], 1)
        self.assertGreaterEqual(totals['claimsWithEvidence'], 1)
        self.assertEqual(payload['summary']['sectionsWithClaims'], 1)
        self.assertGreaterEqual(totals['evidenceItems'], 1)

    def test_claim_bundle_exposes_support_refs_and_levels(self):
        bundle = report_ui.build_claim_bundle(
            text='- Organizers are likely to escalate the campaign next week.',
            locale='en',
            evidence_context={
                'factCards': [
                    {'text': 'Organizers are preparing a larger campaign next week.', 'preview': 'Larger campaign next week.', 'sourceTool': 'insight_forge', 'evidenceId': 'fact_demo_1'}
                ],
                'citationCards': [
                    {'label': 'Primary memo', 'url': 'https://example.com/memo', 'sourceTool': 'insight_forge', 'evidenceId': 'citation_demo_1'}
                ],
                'toolsUsed': ['insight_forge'],
                'queries': ['campaign escalation'],
            }
        )
        self.assertTrue(bundle['claimCards'])
        claim = bundle['claimCards'][0]
        self.assertIn('claimId', claim)
        self.assertIn('supportingRefs', claim)
        self.assertGreaterEqual(claim['supportRefCount'], 1)
        self.assertIn(claim['supportLevel'], {'strong', 'supported', 'light', 'unbacked'})
        self.assertGreaterEqual(bundle['evidenceRefCount'], 1)


if __name__ == '__main__':
    unittest.main()
