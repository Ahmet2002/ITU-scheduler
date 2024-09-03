from bs4 import BeautifulSoup
import requests

html_content = '''<select class="form-control selectpicker" data-live-search="true" name="derskodu" tabindex="-98">
				<option value="">Ders Kodu Seçiniz</option>
				<option value="AKM">AKM</option>
				<option value="ATA">ATA</option>
				<option value="BED">BED</option>
				<option value="BIL">BIL</option>
				<option value="BIO">BIO</option>
				<option value="BLG">BLG</option>
				<option value="BUS">BUS</option>
				<option value="CAB">CAB</option>
				<option value="CEV">CEV</option>
				<option value="CHZ">CHZ</option>
				<option value="CIE">CIE</option>
				<option value="CMP">CMP</option>
				<option value="COM">COM</option>
				<option value="DEN">DEN</option>
				<option value="DFH">DFH</option>
				<option value="DNK">DNK</option>
				<option value="DUI">DUI</option>
				<option value="EAS">EAS</option>
				<option value="EEF">EEF</option>
				<option value="ECO">ECO</option>
				<option value="ECN">ECN</option>
				<option value="EHB" selected="">EHB</option>
				<option value="EHN">EHN</option>
				<option value="EKO">EKO</option>
				<option value="ELE">ELE</option>
				<option value="ELH">ELH</option>
				<option value="ELK">ELK</option>
				<option value="END">END</option>
				<option value="ENR">ENR</option>
				<option value="ENT">ENT</option>
				<option value="ESL">ESL</option>
				<option value="ETH">ETH</option>
				<option value="ETK">ETK</option>
				<option value="EUT">EUT</option>
				<option value="FIZ">FIZ</option>
				<option value="GED">GED</option>
				<option value="GEM">GEM</option>
				<option value="GEO">GEO</option>
				<option value="GID">GID</option>
				<option value="GMI">GMI</option>
				<option value="GSB">GSB</option>
				<option value="GUV">GUV</option>
				<option value="HUK">HUK</option>
				<option value="HSS">HSS</option>
				<option value="ICM">ICM</option>
				<option value="ILT">ILT</option>
				<option value="IML">IML</option>
				<option value="ING">ING</option>
				<option value="INS">INS</option>
				<option value="ISE">ISE</option>
				<option value="ISL">ISL</option>
				<option value="ISH">ISH</option>
				<option value="ITB">ITB</option>
				<option value="JDF">JDF</option>
				<option value="JEF">JEF</option>
				<option value="JEO">JEO</option>
				<option value="KIM">KIM</option>
				<option value="KMM">KMM</option>
				<option value="KMP">KMP</option>
				<option value="KON">KON</option>
				<option value="MAD">MAD</option>
				<option value="MAK">MAK</option>
				<option value="MAL">MAL</option>
				<option value="MAR">MAR</option>
				<option value="MAT">MAT</option>
				<option value="MCH">MCH</option>
				<option value="MEK">MEK</option>
				<option value="MEN">MEN</option>
				<option value="MET">MET</option>
				<option value="MDN">MDN</option>
				<option value="MIM">MIM</option>
				<option value="MMD">MMD</option>
				<option value="MOD">MOD</option>
				<option value="MRT">MRT</option>
				<option value="MRE">MRE</option>
				<option value="MRT">MRT</option>
				<option value="MTO">MTO</option>
				<option value="MTH">MTH</option>
				<option value="MTM">MTM</option>
				<option value="MTR">MTR</option>
				<option value="MST">MST</option>
				<option value="MUH">MUH</option>
				<option value="MUK">MUK</option>
				<option value="MUT">MUT</option>
				<option value="MUZ">MUZ</option>
				<option value="NAE">NAE</option>
				<option value="NTH">NTH</option>
				<option value="PAZ">PAZ</option>
				<option value="PEM">PEM</option>
				<option value="PET">PET</option>
				<option value="PHE">PHE</option>
				<option value="PHY">PHY</option>
				<option value="RES">RES</option>
				<option value="SBP">SBP</option>
				<option value="SAO">SAO</option>
				<option value="SES">SES</option>
				<option value="STA">STA</option>
				<option value="STI">STI</option>
				<option value="TDW">TDW</option>
				<option value="TEB">TEB</option>
				<option value="TEK">TEK</option>
				<option value="TEL">TEL</option>
				<option value="TER">TER</option>
				<option value="TES">TES</option>
				<option value="THO">THO</option>
				<option value="TUR">TUR</option>
				<option value="UCK">UCK</option>
				<option value="UZB">UZB</option>
				<option value="VBA">VBA</option>
				<option value="YTO">YTO</option>
				<option value="YZV">YZV</option>
			</select>'''

# url = 'https://www.sis.itu.edu.tr/TR/ogrenci/lisans/onsartlar/onsartlar.php'
# response = requests.get(url)
# print(response.status_code)

soup = BeautifulSoup(html_content, "html.parser")

# Extract the options from the select element
select_element = soup.find("select", {"name": "derskodu"})

# Initialize a list to store the ids and codes
id_code_list = []

# Loop through the options and extract the values
for option in select_element.find_all("option"):
    dersBransKoduId = option.get("value")
    class_code = option.text.strip()
    if dersBransKoduId and class_code:  # Only add if both are present
        id_code_list.append(dersBransKoduId)

# Print the list of ids and codes
print(id_code_list)