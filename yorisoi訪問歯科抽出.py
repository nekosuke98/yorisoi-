import time
import unicodedata
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ====================================================
# 1. 接続設定（既存のChromeデバッグポートへ接続）
# ====================================================
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# Seleniumが迷子にならないよう、確実にYorisoiのタブを探して切り替える
for handle in driver.window_handles:
    try:
        driver.switch_to.window(handle)
        if "Yorisoi" in driver.title or "患者マスタ" in driver.title:
            break
    except Exception:
        pass

print("==============================")
print(f"現在接続中のページ: {driver.title}")
print("==============================")


# ====================================================
# 2. 安全に値を取得するための関数定義
# ====================================================
def get_value(by, selector, is_input=False):
    try:
        element = driver.find_element(by, selector)
        if is_input:
            return element.get_attribute("value")
        else:
            return element.text
    except Exception:
        return "【取得エラー】"

def get_checkbox_status(label_text):
    try:
        element = driver.find_element(By.XPATH, f"//label[contains(., '{label_text}')]")
        if element.get_attribute("data-checked") is not None:
            return "あり"
        inputs = element.find_elements(By.TAG_NAME, "input")
        if inputs and inputs[0].is_selected():
            return "あり"
        return "なし"
    except Exception:
        return "【取得エラー】"


# ====================================================
# 3. Yorisoi画面からの各項目データ取得
# ====================================================
current_url = driver.current_url

last_name = get_value(By.ID, "lastNameInput", is_input=True)
first_name = get_value(By.ID, "firstNameInput", is_input=True)
last_name_kana = get_value(By.ID, "lastNameKanaInput", is_input=True)
first_name_kana = get_value(By.ID, "firstNameKanaInput", is_input=True)
birthday = get_value(By.ID, "birthdayInput", is_input=True)

age_xpath = "//*[@id='birthdayInput']/following::p[1]"
age_text = get_value(By.XPATH, age_xpath, is_input=False)

facility_xpath = "//*[contains(text(), '所属施設') and not(*)]/following::div[string-length(text()) > 0][1]"
facility_name = get_value(By.XPATH, facility_xpath, is_input=False)

public_insurance_xpath = "//*[contains(text(), '公費医療証') and not(.//*[contains(text(), '公費医療証')])]/following::label[@data-checked][1]"
public_insurance_text = get_value(By.XPATH, public_insurance_xpath, is_input=False)

insurance_xpath = "//*[contains(text(), '医療保険証') and not(.//*[contains(text(), '医療保険証')])]/following::label[@data-checked][1]"
insurance_text = get_value(By.XPATH, insurance_xpath, is_input=False)

limit_cert = get_checkbox_status("限度額認定証")

nursing_burden_xpath = "//*[contains(text(), '介護保険負担割合証') and not(.//*[contains(text(), '介護保険負担割合証')])]/following::label[@data-checked][1]"
nursing_burden_text = get_value(By.XPATH, nursing_burden_xpath, is_input=False)

medical_expense = get_value(By.ID, "medicalExpense", is_input=True)
oral_consent_date = get_value(By.ID, "oralConsentDateInput", is_input=True)
basic_remarks = get_value(By.ID, "remarksInput", is_input=True)

care_manager_office = get_value(By.ID, "careManagerOfficeNameInput", is_input=True)
care_manager_fax = get_value(By.ID, "careManagerFaxInput", is_input=True)
care_manager_name = get_value(By.ID, "careManagerNameInput", is_input=True)
key_person_remarks = get_value(By.ID, "keyPerson1RemarksInput", is_input=True)


# ====================================================
# 4. 取得したテキストの整形・ターミナル出力
# ====================================================
output_text = (
    f"所属施設 ：{facility_name}\n"
    f"氏名     ：{last_name}{first_name}\n"
    f"かな     ：{last_name_kana}{first_name_kana}\n"
    f"生年月日 ：{birthday}\n"
    f"和暦     ：{age_text}\n"
    f"公費医療証        ：{public_insurance_text}\n"
    f"介護保険負担割合証：{nursing_burden_text}\n"
    f"医療保険証        ：{insurance_text}\n"
    f"限度額認定証      ：{limit_cert}\n"
    f"診療費用    ：{medical_expense}\n"
    f"口頭同意日  ：{oral_consent_date}\n"
    f"基本情報備考：\n{basic_remarks}\n"
    f"\n"
    f"ケアマネ事業所名：{care_manager_office}\n"
    f"ケアマネ氏名    ：{care_manager_name}\n"
    f"ケアマネＦＡＸ  ：{care_manager_fax}\n"
    f"キーパーソン備考：\n{key_person_remarks}\n"
    f"━━━━━━━━━━━━━━━━━━━━━━\n"
    f"患者ページ；{current_url}"
)

print("▼ 取得結果 ▼")
print(output_text)
print("------------")


# ====================================================
# 5. ローカルテキストファイルへの保存
# ====================================================
try:
    desktop_path = "/Users/ccd_bs_001/Desktop/抽出データ.txt"
    with open(desktop_path, mode="w", encoding="utf-8") as f:
        f.write(output_text)
    print(f"テキストファイルに出力しました: {desktop_path}")
except Exception as e:
    print(f"ファイルの保存に失敗しました: {e}")


# ====================================================
# 6. Googleフォームへの自動転記処理
# ====================================================
print("Googleフォームへ転記を開始します...")

try:
    # 本番用GoogleフォームURL
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdJ5WY2xxcGtOV2KC4CRRqi4C4mZCb2xvsct3Nm6KjB5cGhyQ/viewform"
    
    driver.switch_to.new_window('tab')
    driver.get(form_url)
    time.sleep(3)

    # 抽出していない変数は空欄にしてエラーを回避
    chief_complaint = ""

    # ----------------------------------------------------
    # 【1_1 / 1_2】施設名の自動選択（表記ゆれ・複数リスト対応）
    # ----------------------------------------------------
    dropdown_1_1_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[3]/div/div/div[2]/div/div[1]/div[1]/div[1]/span'
    dropdown_1_2_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[4]/div/div/div[2]/div/div[1]/div[1]/div[1]/span'

    if facility_name and facility_name != "【取得エラー】":
        facility_selected = False
        
        # 検索キーワードの表記ゆれ（「デ」と「テ゛」など）をNFC形式に正規化
        search_keyword = unicodedata.normalize('NFC', facility_name)

        # --- ① 「1_1 CCDC大野城」のリストから探索 ---
        try:
            driver.find_element(By.XPATH, dropdown_1_1_xpath).click()
            time.sleep(1)
            
            options = driver.find_elements(By.XPATH, '//div[@role="option"]')
            for opt in options:
                if opt.text:
                    opt_text_normalized = unicodedata.normalize('NFC', opt.text)
                    if search_keyword in opt_text_normalized:
                        opt.click()
                        print(f"【大野城】のリストから '{opt.text}' を選択しました。")
                        facility_selected = True
                        time.sleep(0.5)
                        break
            
            # --- ② 見つからなければ閉じて「1_2 CCDC糸島」から探索 ---
            if not facility_selected:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)

                driver.find_element(By.XPATH, dropdown_1_2_xpath).click()
                time.sleep(1)
                
                options = driver.find_elements(By.XPATH, '//div[@role="option"]')
                for opt in options:
                    if opt.text:
                        opt_text_normalized = unicodedata.normalize('NFC', opt.text)
                        if search_keyword in opt_text_normalized:
                            opt.click()
                            print(f"【糸島】のリストから '{opt.text}' を選択しました。")
                            facility_selected = True
                            time.sleep(0.5)
                            break
                
                if not facility_selected:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    print(f"※施設 '{facility_name}' に一致する選択肢が見つかりませんでした。")
                    
        except Exception as e:
            print(f"施設名の選択中にエラーが発生しました: {e}")

    # ----------------------------------------------------
    # 各テキスト項目の自動入力
    # ----------------------------------------------------
    # 【1_3】患者名
    form_name_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[5]/div/div/div[2]/div/div[1]/div/div[1]/input'
    driver.find_element(By.XPATH, form_name_xpath).send_keys(last_name + " " + first_name)

    # 【1_4】主訴（空欄）
    form_chief_complaint_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[6]/div/div/div[2]/div/div[1]/div[2]/textarea'
    driver.find_element(By.XPATH, form_chief_complaint_xpath).send_keys(chief_complaint)

    # 【1_9】ケアマネ情報（事業所名_FAX）
    form_care_office_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[11]/div/div/div[2]/div/div[1]/div[2]/textarea'
    merged_care_info = f"{care_manager_office}_{care_manager_fax}"
    driver.find_element(By.XPATH, form_care_office_xpath).send_keys(merged_care_info)

    # 【1_10】ケアマネ情報（担当者名）
    form_care_name_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[12]/div/div/div[2]/div/div[1]/div/div[1]/input'
    driver.find_element(By.XPATH, form_care_name_xpath).send_keys(care_manager_name)

    # 【1_11】その他（キーパーソン備考 ＋ 患者ページURL）
    form_remarks_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[13]/div/div/div[2]/div/div[1]/div[2]/textarea'
    combined_remarks = (
        f"{key_person_remarks}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"患者ページ；{current_url}"
    )
    driver.find_element(By.XPATH, form_remarks_xpath).send_keys(combined_remarks)

    print("本番フォームへの自動入力が完了しました！")

except Exception as e:
    print(f"フォームの入力に失敗しました:\n{e}")