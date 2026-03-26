import { useState } from 'react';
import { AlertTriangle, ChevronDown, HelpCircle, Shield } from 'lucide-react';

export interface CounterQuestion {
  id: string;
  question: string;
  type: string;
  criticality: string;
  rationale: string;
  alternative_hypothesis?: string;
  impact_if_true: string;
}

export interface CounterAnalysis {
  counter_questions: CounterQuestion[];
  assumption_challenges: Array<{
    assumption: string;
    why_questionable: string;
    counter_scenario: string;
    probability_if_false: number;
  }>;
  evidence_gaps: string[];
  alternative_interpretations: Array<{
    interpretation: string;
    probability: string;
    implications: string;
  }>;
  confidence_adjustment?: {
    recommended_adjustment: number;
    recommendation: string;
    reasoning: string;
  };
  red_team_summary: string;
}

const criticalityColors: Record<string, string> = {
  fundamental: 'border-red-500/50 bg-red-900/20',
  significant: 'border-orange-500/50 bg-orange-900/20',
  moderate: 'border-yellow-500/50 bg-yellow-900/20',
  minor: 'border-blue-500/50 bg-blue-900/20',
};

export default function RedTeamSection({ counterAnalysis }: { counterAnalysis: CounterAnalysis }) {
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-red-500/30 bg-red-900/20 p-4">
        <div className="mb-2 flex items-center gap-2">
          <Shield className="h-5 w-5 text-red-400" />
          <span className="text-sm font-semibold text-red-300">Red Team Assessment</span>
        </div>
        <div className="whitespace-pre-wrap text-sm text-slate-300">{counterAnalysis.red_team_summary}</div>
      </div>

      {counterAnalysis.confidence_adjustment && (
        <div
          className={`rounded-lg border p-3 ${
            counterAnalysis.confidence_adjustment.recommendation === 'maintain'
              ? 'border-green-500/30 bg-green-900/20'
              : counterAnalysis.confidence_adjustment.recommendation === 'reduce'
                ? 'border-amber-500/30 bg-amber-900/20'
                : 'border-red-500/30 bg-red-900/20'
          }`}
        >
          <div className="mb-1 text-xs font-semibold text-slate-300">
            Confidence Adjustment: {counterAnalysis.confidence_adjustment.recommendation.toUpperCase()}
          </div>
          <div className="text-xs text-slate-400">{counterAnalysis.confidence_adjustment.reasoning}</div>
          {counterAnalysis.confidence_adjustment.recommended_adjustment < 0 && (
            <div className="mt-2 text-xs text-amber-400">
              Suggest reducing confidence by{' '}
              {Math.abs(counterAnalysis.confidence_adjustment.recommended_adjustment * 100).toFixed(0)} percentage points
            </div>
          )}
        </div>
      )}

      {counterAnalysis.counter_questions?.length > 0 && (
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Critical Counter-Questions ({counterAnalysis.counter_questions.length})
          </div>
          <div className="space-y-2">
            {counterAnalysis.counter_questions.map((question) => (
              <div
                key={question.id}
                className={`overflow-hidden rounded-lg border ${criticalityColors[question.criticality] || criticalityColors.moderate}`}
              >
                <button
                  onClick={() => setExpandedQuestion(expandedQuestion === question.id ? null : question.id)}
                  className="w-full p-3 text-left transition-colors hover:bg-slate-700/20"
                >
                  <div className="flex items-start gap-2">
                    <HelpCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-400" />
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 text-sm text-slate-200">{question.question}</div>
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-slate-700/50 px-1.5 py-0.5 text-[10px] uppercase text-slate-400">
                          {question.type.replace(/_/g, ' ')}
                        </span>
                        <span className="rounded bg-slate-700/50 px-1.5 py-0.5 text-[10px] uppercase text-amber-400">
                          {question.criticality}
                        </span>
                      </div>
                    </div>
                    <ChevronDown
                      className={`h-4 w-4 text-slate-500 transition-transform ${expandedQuestion === question.id ? 'rotate-180' : ''}`}
                    />
                  </div>
                </button>
                {expandedQuestion === question.id && (
                  <div className="space-y-2 px-3 pb-3 text-xs">
                    <div>
                      <span className="text-slate-500">Rationale:</span>
                      <div className="mt-1 text-slate-300">{question.rationale}</div>
                    </div>
                    {question.alternative_hypothesis && (
                      <div>
                        <span className="text-slate-500">Alternative:</span>
                        <div className="mt-1 text-slate-300">{question.alternative_hypothesis}</div>
                      </div>
                    )}
                    <div>
                      <span className="text-slate-500">Impact if true:</span>
                      <div className="mt-1 text-amber-300">{question.impact_if_true}</div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {counterAnalysis.assumption_challenges?.length > 0 && (
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Questionable Assumptions</div>
          <div className="space-y-2">
            {counterAnalysis.assumption_challenges.map((challenge, index) => (
              <div key={`${challenge.assumption}-${index}`} className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-3">
                <div className="mb-2 text-sm font-medium text-slate-200">{challenge.assumption}</div>
                <div className="mb-2 text-xs text-slate-400">{challenge.why_questionable}</div>
                <div className="text-xs">
                  <span className="text-slate-500">Alternative scenario:</span>
                  <div className="mt-1 text-amber-300">{challenge.counter_scenario}</div>
                </div>
                <div className="mt-2 text-xs text-red-400">
                  Probability this assumption is false: {(challenge.probability_if_false * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {counterAnalysis.evidence_gaps?.length > 0 && (
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Critical Evidence Gaps</div>
          <div className="space-y-1">
            {counterAnalysis.evidence_gaps.map((gap, index) => (
              <div key={`${gap}-${index}`} className="flex items-start gap-2 text-xs text-slate-300">
                <AlertTriangle className="mt-0.5 h-3 w-3 flex-shrink-0 text-amber-400" />
                {gap}
              </div>
            ))}
          </div>
        </div>
      )}

      {counterAnalysis.alternative_interpretations?.length > 0 && (
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Alternative Interpretations</div>
          <div className="space-y-2">
            {counterAnalysis.alternative_interpretations.map((interpretation, index) => (
              <div key={`${interpretation.interpretation}-${index}`} className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-3">
                <div className="mb-1 text-sm text-cyan-300">{interpretation.interpretation}</div>
                <div className="mb-1 text-xs text-slate-400">Probability: {interpretation.probability}</div>
                <div className="text-xs text-slate-300">{interpretation.implications}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
