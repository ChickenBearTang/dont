/**
 * AI 서버가 응답의 warnings 에 담아 보내는 코드를 사용자에게 보여줄 한국어 문장으로 바꾼다.
 *
 * 코드는 두 가지 모양이다.
 *   - 고정 코드:  PRICE_MODEL_UNTRUSTED
 *   - 세부가 붙은 코드:  FINANCE_FIELD_DEFAULTED:monthly_spending_30d  (콜론 앞이 종류, 뒤가 대상/이유)
 * 매핑에 없는 코드는 코드 그대로 두지 않고 일반 안내 문장 + 괄호 속 코드로 보여준다
 * (영어 내부 코드가 화면에 그대로 나가지 않게 하되, 문의할 때 단서는 남긴다).
 */

const fixedWarningLabels: Record<string, string> = {
  // 가격 이력·크롤링
  CRAWL_FETCH_FAILED: '상품 페이지 크롤링에 실패했어요.',
  PRICE_ESTIMATED_FROM_REQUEST: '요청 가격 기준으로 대체 계산했어요.',
  NO_PRICE_HISTORY: '가격 이력이 부족해서 요청 가격을 평균가처럼 썼어요.',
  PRICE_HISTORY_READ_FAILED: '가격 이력을 불러오지 못했어요.',
  MISSING_PURCHASE_URL: '구매 링크가 없어 크롤링을 건너뛰었어요.',
  ITEM_FAMILY_UNCLASSIFIED: '품목 종류를 알아내지 못해 가격 이력을 찾지 못했어요.',
  PRICE_ONLY_FALLBACK: '재무 정보 없이 가격만 보고 판단했어요.',
  // 모델·설명 엔진
  PRICE_MODEL_UNTRUSTED: '가격 예측 모델은 아직 믿을 만한 수준이 아니라 판단에 쓰지 않았어요.',
  SHAP_UNAVAILABLE: '근거 계산(SHAP)을 사용할 수 없어요.',
  SHAP_ERROR: '근거 계산(SHAP) 중 오류가 났어요.',
  DICE_UNAVAILABLE: '대안 제안(DiCE)을 사용할 수 없어요.',
  DICE_ERROR: '대안 제안(DiCE) 중 오류가 났어요.',
  DICE_INIT_FAILED: '대안 제안(DiCE)을 준비하지 못했어요.',
  DICE_EMPTY: '바꿔 볼 만한 대안을 찾지 못했어요.',
  DICE_NO_CHANGE: '조건을 바꿔도 판단이 달라지지 않았어요.',
  MODEL_LOAD_FAILED: '예측 모델을 불러오지 못했어요.',
  MODEL_PREDICT_FAILED: '예측 모델 계산에 실패했어요.',
  MODEL_PATH_MISSING: '예측 모델 파일을 찾지 못했어요.',
  FEATURE_SCHEMA_MISMATCH: '예측 모델의 입력 형식이 맞지 않아요.',
  SCHEMA_VERSION_MISMATCH: '예측 모델의 버전이 맞지 않아요.',
  TARGET_SCHEMA_MISMATCH: '예측 모델의 대상 형식이 맞지 않아요.',
  INFERENCE_PAYLOAD_INVALID: '예측 모델에 넘길 입력이 올바르지 않아요.',
  PANDAS_UNAVAILABLE: '예측 계산에 필요한 구성요소가 없어요.',
  NOT_COMPUTED: '이 항목은 계산하지 않았어요.',
  // 재무 입력
  FINANCE_PROFILE_EMPTY_FALLBACK: '재무 데이터가 부족해 가격 중심으로 판단했어요.',
  SPENDING_TRUNCATED:
    '최근 거래가 많아 일부만 집계됐어요. 월 지출이 실제보다 적게 잡혔을 수 있어요.',
  EMERGENCY_COVER_LOW: '비상금이 3개월치 생활비보다 적어요.',
  // 입력 검증 오류
  XAI_ITEM_VALIDATION_FAILED: '이 품목의 계산 결과가 검증을 통과하지 못했어요.',
  XAI_INPUT_CONTRACT_VIOLATION: '전달된 재무 정보의 형식이 올바르지 않아요.',
  XAI_ANALYSIS_FAILED: '분석 중 오류가 나서 일부 결과를 만들지 못했어요.',
};

/** 재무 입력 필드 이름 (AI 서버의 snake_case). */
const financeFieldLabels: Record<string, string> = {
  current_balance: '현재 잔액',
  emergency_fund_balance: '비상금',
  savebox_balance: '세이브박스 잔액',
  expected_card_payment_amount: '이번 달 카드 결제 예정액',
  days_until_card_due: '카드 결제일까지 남은 일수',
  available_fixed_income: '월 소득',
  available_fixed_expense: '월 고정지출',
  monthly_spending_30d: '최근 30일 지출',
};

/** 월 지출을 거래 내역에서 못 구한 이유. */
const spendingUnknownReasonLabels: Record<string, string> = {
  no_transactions: '카드 거래 내역이 없어요.',
  no_spending_in_window: '최근 30일 안에 카드 거래가 없어요.',
  unparseable: '카드 거래 내역을 읽지 못했어요.',
};

/** 5·3·2 예산 규칙을 적용하지 못한 이유 (AI 서버: analyzer 의 *_not_provided_by_upstream, budget_rule 의 *_unknown). */
const budgetUnavailableReasonLabels: Record<string, string> = {
  income_not_provided_by_upstream: '월 소득 정보를 받지 못했어요.',
  fixed_expense_not_provided_by_upstream: '월 고정지출 정보를 받지 못했어요.',
  spending_not_provided_by_upstream: '최근 30일 지출 정보를 받지 못했어요.',
  income_unknown_or_not_positive: '월 소득을 알 수 없거나 0원 이하예요.',
  fixed_expense_unknown: '월 고정지출을 알 수 없어요.',
  spending_unknown: '최근 30일 지출을 알 수 없어요.',
  price_invalid: '가격 정보가 올바르지 않아요.',
};

const fieldLabel = (field: string): string => financeFieldLabels[field] ?? field;

const detailLabel = (kind: string, detail: string): string | null => {
  switch (kind) {
    case 'FINANCE_FIELD_DEFAULTED':
      return `${fieldLabel(detail)} 정보를 받지 못해 기본값으로 계산했어요.`;
    case 'FINANCE_FIELD_ESTIMATED':
      return `${fieldLabel(detail)}은(는) 계좌 내역에서 추정한 값이에요.`;
    case 'SPENDING_UNKNOWN':
      return `최근 30일 지출을 계산하지 못했어요. ${spendingUnknownReasonLabels[detail] ?? ''}`.trim();
    case 'BUDGET_RULE_UNAVAILABLE':
      return `5·3·2 예산 판단을 하지 못했어요. ${budgetUnavailableReasonLabels[detail] ?? ''}`.trim();
    case 'FINANCE_EXPLANATION_UNAVAILABLE':
      return '재무 상태에 대한 근거 설명을 만들지 못했어요.';
    default:
      return null;
  }
};

export const getXaiWarningLabel = (warning: string): string => {
  const fixed = fixedWarningLabels[warning];
  if (fixed) return fixed;

  const separator = warning.indexOf(':');
  if (separator > 0) {
    const labeled = detailLabel(warning.slice(0, separator), warning.slice(separator + 1));
    if (labeled) return labeled;
  }
  return `확인이 필요한 안내가 있어요. (${warning})`;
};
