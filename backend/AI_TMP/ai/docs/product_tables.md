# 상품 카탈로그 · 별칭 · 유통경로(직구/병행수입) 테이블

한국 인증 기관(KC/전파 적합성평가) 기록을 기준으로 상품을 정하고, 그 위에 **사람이 부르는 이름(별칭)** 과
**유통경로 규칙(직구/병행수입 등)** 을 별도 테이블로 얹는다. 목적은 "로지텍 MX Master 3S"와 "MX Master 3"처럼
이름이 비슷한 모델을 섞지 않으면서, "MX Master S3", "마스터 3S" 같은 실제 표기를 같은 상품으로 알아보는 것이다.

## 한눈에

| 테이블 | 한 줄의 뜻 | 누가 채우나 |
|---|---|---|
| `product_catalog` | 인증 기관 기준 상품. 인증 기록의 기본모델 하나가 한 줄 | KC 가져오기(`import_kc_catalog`), 시드, 직구 전용 상품은 사람 |
| `product_aliases` | 그 상품을 가리키는 이름: 마케팅 이름, 한글 표기, 줄임말, 통칭, 뒤집힌 표기 | 사람(검수), 크롤 데이터에서 제안(`pending`) |
| `sourcing_categories` | 유통경로(정식수입/병행수입/해외직구/구매대행)와 그 경로의 규칙. **Y/N 열** | 사람 |
| `sourcing_signals` | 제목/주소에서 경로를 알아내는 신호(키워드, 토큰, 도메인) | 사람 |

DDL: `crawler/identity/sql/product_tables_v1.sql` (PostgreSQL, 여러 번 실행해도 안전). 같은 열의 CSV 4개
(`crawler/identity/data/tables/`)로도 쓸 수 있다. DB 없이 개발/검수할 때, 또는 사람이 엑셀로 주고받을 때 쓴다.

## 1. 카탈로그와 별칭

### 왜 별칭을 따로 두나
인증 기록에는 `SM-R510` 같은 규제용 모델 코드가 있고 "갤럭시 버즈2 프로"라는 이름은 없다. 같은 상품을 사람마다
다르게 부르고(`MX Master 3S`, `MX Master S3`, `엠엑스 마스터 3S`, `마스터 3S`), 비슷한 모델도 있다(`3`, `3S`, `4`).
그래서 이름은 **유사도로 맞추지 않고**, 사람이 승인한 이름만 **토큰 경계에서 정확히** 일치할 때 쓴다.
(`마스터 3` 이름이 "마스터 3S" 제목의 앞부분에 걸려 3 으로 잘못 붙는 일이 없다.)

### 별칭 한 줄의 열
| 열 | 값 | 뜻 |
|---|---|---|
| `alias_text` | 사람이 쓴 그대로 | `MX Master S3` |
| `alias_kind` | `model` / `line` | `model`: 이 상품 하나를 가리킴. `line`: 제품군 이름("엠엑스 마스터")이라 여러 상품에 걸침. 제목에 이것만 있으면 하나를 고르지 않고 후보로만 돌려준다(`ambiguous_variant`) |
| `alias_type` | `marketing` `korean` `english` `abbreviation` `colloquial` `misspelling` `kc_derived` `part_number` `other` | 어떤 이름인가. 식별 근거에 남는다: `catalog code 'mxmasters3' (alias: misspelling)` |
| `brand_required_yn` | `Y` / `N` | `Y`: 제목에 그 브랜드가 있을 때만 이 이름을 인정. 짧거나 통칭인 이름("마스터 3S")이 다른 브랜드 글에서 맞는 것을 막는다 |
| `status` | `approved` / `pending` / `rejected` | **`approved` 만 매칭에 쓴다.** 새 행의 기본은 `pending`. `rejected` 는 "이 이름은 아니다"를 기억해 다시 제안하지 않게 하는 기록 |
| `source` | `curated` `kc` `crawl_suggested` `llm_suggested` `user_report` | 어디서 왔나 |

### 막는 것 (검증, `tables/validate.py`)
검증에서 걸린 행은 쓰지 않고 이유를 보고한다. 한 줄이 틀렸다고 전체가 멈추지도, 틀린 행이 조용히 들어가지도 않는다.

- 같은 이름을 **두 상품이 정확한 이름으로** 주장(`ALIAS_CONFLICT`): 어느 쪽인지 알 수 없어 둘 다 쓰지 않는다.
  정말 여러 상품에 걸친 이름이면 `alias_kind=line` 으로 쓴다. DB 에서는 뷰 `v_product_alias_conflicts` 로도 볼 수 있다.
- 다른 상품의 **모델 코드와 같은 이름**(`ALIAS_CONFLICT`).
- **너무 짧거나 숫자뿐인 이름**(`ALIAS_TOO_GENERIC`): 4자 미만이거나 숫자뿐이면 `brand_required_yn=Y` 여야 한다.
- 없는 상품을 가리키는 별칭(`ALIAS_ORPHAN`), 허용되지 않는 값(`ALIAS_BAD_VALUE`), 같은 이름 중복(`ALIAS_DUPLICATE`),
  자기 모델 코드와 같은 별칭(`ALIAS_SAME_AS_MODEL`, 경고).
- `pending` 별칭이 승인하면 충돌할 경우 경고(`PENDING_ALIAS_WOULD_CONFLICT`)만 하고 남긴다. 검수자가 보도록.

### 예: MX Master
```
logitech:mx-master-3s   MX Master S3        model  misspelling  N  approved   3S 를 S3 로 뒤집어 쓰는 표기
logitech:mx-master-3s   마스터 3S            model  colloquial   Y  approved   브랜드가 제목에 있을 때만
logitech:mx-master-3    마스터 3             model  colloquial   Y  approved
logitech:mx-master-*    엠엑스 마스터         line   korean       N  approved   제품군 이름: 후보로만
```
| 제목 | 결과 |
|---|---|
| 로지텍 MX Master S3 무선 마우스 | `mx-master-3s` (alias: misspelling) |
| 로지텍 마스터 3S 마우스 | `mx-master-3s` (3 으로 잘못 붙지 않음) |
| 로지텍 마스터 3 마우스 | `mx-master-3` |
| 마스터 3S 마우스 / 삼성 마스터 3S | 고르지 않음 (브랜드 조건) |
| 로지텍 엠엑스 마스터 무선 마우스 | `ambiguous_variant`, 후보 4개 |

`MX Master S3` 라는 제품이 실제로 없다는 것은 내 기억에 의존한 판단이라 **검수가 필요하다**(`note` 에 적어 두었다).

## 2. 유통경로 규칙 (`sourcing_categories` + `sourcing_signals`)

### 왜 필요한가
같은 상품이어도 직구/병행수입은 관부가세, 배송, 보증이 달라 **가격 수준이 다르다**. 섞어서 가격 이력을 쌓으면 "싼 가격"이
사실은 다른 경로의 가격이다. 그리고 직구 상품은 국내 인증 DB 에 기록이 없는 것이 정상이라, 기록이 없다고 해서 카탈로그가
비어 있는 것으로 취급하면 안 된다.

### 경로(카테고리)와 Y/N 열
| category_code | 라벨 | `kc_record_expected_yn` | `price_pool_yn` |
|---|---|---|---|
| `OFFICIAL_IMPORT` | 정식수입(국내 정발) | Y | Y |
| `PARALLEL_IMPORT` | 병행수입 | U | N |
| `DIRECT_PURCHASE` | 해외직구 | N | N |
| `PURCHASING_AGENCY` | 구매대행 | U | N |

- `kc_record_expected_yn` (`Y`/`N`/`U`=모름): 이 경로의 상품이 인증 DB 에 기록이 있을 것으로 **기대**하는가.
  `Y` 인데 카탈로그에 인증 기록이 연결된 항목이 없으면 `KC_RECORD_EXPECTED_BUT_MISSING` 경고(카탈로그 공백 신호).
  `N`(직구)이나 `U` 면 경고하지 않는다.
- `price_pool_yn` (`Y`/`N`): 가격 이력을 같은 상품의 다른 경로 가격과 **합쳐도 되는가**. `N` 이면
  `ProductIdentity.series_key` 가 `상품ID|경로`(예: `logitech:mx-master-3s|direct_purchase`)로 나뉜다.
  상품 ID(`canonical_id`)는 그대로다: 같은 상품이되 가격 이력만 따로 쌓는다.
- `reviewed_yn`: 사람이 확인한 값인가. **초기 4개 행은 모두 `N`(내 초기 가정)** 이다. 아래 "확인해야 할 것" 참고.

### 신호 한 줄
| 열 | 값 |
|---|---|
| `match_type` | `keyword`: 제목(공백/기호 무시)에 포함 — `직구` 는 해외직구, 직구템에도 맞는다. `token`: 제목의 토큰이 정확히 같을 때(짧은 영문 `ebay`; `freebay` 에는 안 맞는다). `domain`: 주소의 호스트가 같거나 그 하위 도메인(`aliexpress.com` -> `ko.aliexpress.com`) |
| `pattern` | 패턴. 도메인은 호스트 이름만(주소 전체/경로는 거부) |
| `priority` | 작을수록 먼저. 일치한 신호 중 **가장 작은 값끼리만** 판정한다 |
| `enabled_yn` | `N` 이면 쓰지 않는다 |

판정은 추측하지 않는다.
1. 신호가 없으면 경로는 `None` 이다. **경로를 모른다고 국내 판매로 가정하지 않는다.**
2. 가장 작은 priority 의 신호들이 한 경로를 가리키면 그 경로, **서로 다른 경로면 `SOURCING_CONFLICT` 로 알리고 고르지 않는다**
   (예: `병행 직구`). 이때 상품 식별은 영향받지 않는다.
3. 같은 신호를 서로 다른 경로로 적은 행은 모두 쓰지 않는다(`SIGNAL_CONFLICT`).

초기 신호(패키지 `sourcing_signals.csv`, 24개): 도메인(aliexpress, amazon.com/.co.jp/.de, ebay, taobao, iherb; priority 10),
키워드(`직구`, `알리익스프레스`, `아마존`, `이베이`, `타오바오`, `관부가세`, `배대지`, `병행`, `구매대행`(priority 40),
`정발`, `정식발매`, `정식수입`, `공식수입`), 토큰(`aliexpress`, `amazon`, `ebay`, `taobao`). 전부 내가 알고 있는 쇼핑 용어에서
고른 **초기 값이고 실제 수집 제목으로 검증하지 않았다.** 예: `병행` 은 `병행수입`/`병행품`에 모두 맞지만 다른 뜻으로 쓰인
글에도 맞을 수 있다.

### 식별 결과에 붙는 것
`ProductResolver.resolve(title, url=...)` 의 `ProductIdentity`:
`sourcing_status`(`classified`/`conflict`/`none`), `sourcing_category`, `price_pool`, `sourcing_evidence`, `series_key`.
`url` 을 주면 도메인 신호도 쓴다(크롤러와 가격 정규화기가 넘긴다).

## 3. 어디서 읽나 (`tables/loader.py`)

하나만 쓴다. 우선순위:

1. `AI_PRODUCT_TABLES_DSN` — PostgreSQL 에서 읽는다. **읽지 못하면 조용히 비우지 않고 예외**를 낸다.
2. `AI_PRODUCT_TABLES_DIR` — CSV 4개가 든 디렉터리.
3. (없으면) 패키지 초기 파일 `crawler/identity/data/tables/` — 별칭 21개, 경로 4개, 신호 24개. 카탈로그는 시드 JSON.

항상 먼저 읽는 파일 카탈로그(시드 `catalog_seed.json` + `AI_PRODUCT_CATALOG_PATHS` 의 KC 결과) **위에 테이블을 얹는다.**
- 테이블의 카탈로그 행은 같은 id 의 파일 항목을 **대체한다**(DB 에서 고친 값이 우선). 대체된 항목은 파일의 인라인 별칭을
  이어받지 않는다: 별칭은 테이블에서만 오므로 DB 에서 거절한 별칭이 파일 때문에 되살아나지 않는다.
- 별칭은 승인된 것만 붙는다. 충돌하는 별칭은 붙이지 않고 `catalog.issues` 에 남는다.

## 4. 운영 순서

```bash
cd backend/AI_TMP
export AI_PRODUCT_TABLES_DSN=postgresql://user:pw@host:5432/db

python -m ai.scripts.catalog_tables init-db                    # 테이블/뷰 (여러 번 실행해도 안전)
python -m ai.scripts.catalog_tables import --seed --dry-run    # 가져올 내용 검증만 (DB 는 읽기만)
python -m ai.scripts.catalog_tables import --seed              # 시드 카탈로그 + 초기 별칭/규칙
python -m ai.scripts.import_kc_catalog --input rra.csv --output catalog_kc.json   # KC 파일 -> 카탈로그 JSON
python -m ai.scripts.catalog_tables import --catalog-json catalog_kc.json         # KC 결과를 카탈로그 행 + kc_derived 별칭으로
python -m ai.scripts.catalog_tables export --out dump/         # 검수용 CSV
python -m ai.scripts.catalog_tables validate --csv-dir dump/ --seed
```
- 가져오기는 기본이 **없는 행만 넣기**다. DB 에서 사람이 고친 별칭 상태/경로 규칙을 덮어쓰지 않는다. 덮어쓰려면 `--update` 를 명시한다.
- 한 번의 가져오기는 한 트랜잭션이다. 검증에서 걸린 행은 DB 에 넣지 않고 `issues` 에 이유를 적고, 오류가 있으면 종료 코드가 2 다.
- JSON 카탈로그(시드, KC 결과)에만 있는 상품에 별칭을 붙이려면 **먼저 카탈로그 행으로 옮겨야 한다**(`--seed`,
  `--catalog-json`): DB 의 별칭은 외래키로 카탈로그 행을 가리킨다.

새 별칭 제안 -> 검수: 크롤 데이터에서 해결되지 않은 제목(`export_unresolved_titles`)을 보고 `status=pending` 행을 넣고,
승인하면 `approved` 로 바꾼다. (제목에서 별칭 후보를 자동으로 뽑는 도구는 아직 없다.)

## 5. 확인해야 할 것 / 한계

- **경로 규칙의 Y/N 값은 초기 가정**이다(`reviewed_yn=N`). 특히 `PARALLEL_IMPORT`/`PURCHASING_AGENCY` 의 `kc_record_expected_yn`
  을 `U` 로 둔 이유는 법적 요건을 내가 확인하지 못했기 때문이다. 이 값은 법적 판단이 아니라 "카탈로그 공백 경고를 낼지"를 정하는
  운영 설정이다. 담당자가 확인해서 `reviewed_yn=Y` 로 바꾼다.
- `price_pool_yn=N` 으로 나뉘는 `series_key` 는 **식별 결과에만 있다.** 가격 이력을 쌓는 쪽(`price_engine` 의 데이터셋 빌더,
  `PostgresCrawlStore`)은 아직 이 키로 묶지 않는다.
- 초기 별칭 21개는 시드 상품(검수되지 않은 예시)에 붙은 것이다. KC 데이터를 가져오면 `product_catalog` 는 인증 기록 기준
  항목이 되지만 마케팅 이름은 여전히 사람이 별칭으로 이어 줘야 한다.
- 직구 전용 상품(국내 인증 기록이 없는)은 `product_catalog` 에 `source='import_only'`, `kc_certified_yn='N'` 행으로 직접 넣는다.
  자동으로 만들어 주는 도구는 없다.
- `kc_certified_yn`: `Y` 인증 DB 기록 있음, `N` 없음, `U` 확인 안 함. 시드는 `U` 다.
- 키워드 신호는 한국어 활용(`직구템`, `직구가`)을 위해 부분 일치다. 다른 뜻으로 쓰인 글에 맞을 수 있어 실제 제목으로 오탐을 확인해야 한다.
- 테스트: `ai/tests/test_identity_tables_*.py`, `test_identity_sourcing.py`, `test_catalog_tables_cli.py`. PostgreSQL 서버
  바이너리(`initdb`)가 있으면 임시 서버를 띄워 DDL 제약과 가져오기를 실제로 검증하고, 없으면 그 부분만 건너뛴다.
