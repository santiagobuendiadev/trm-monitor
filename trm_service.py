import urllib.request
import xml.etree.ElementTree as ET
import ssl
from datetime import datetime

class TRMService:
    # The correct endpoint found from working implementations
    ENDPOINT = "https://www.superfinanciera.gov.co/SuperfinancieraWebServiceTRM/TCRMServicesWebService/TCRMServicesWebService"

    def get_current_trm(self, date=None):
        """
        Fetches the TRM from Superfinanciera using only standard library (urllib).
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        soap_payload = f"""<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
    <Body>
        <queryTCRM xmlns="http://action.trm.services.generic.action.superfinanciera.nexura.sc.com.co/">
            <tcrmQueryAssociatedDate xmlns="">{date}</tcrmQueryAssociatedDate>
        </queryTCRM>
    </Body>
</Envelope>"""

        headers = {
            'Content-Type': 'text/xml;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            # Create a context that ignores SSL verification
            context = ssl._create_unverified_context()
            
            req = urllib.request.Request(
                self.ENDPOINT, 
                data=soap_payload.encode('utf-8'), 
                headers=headers, 
                method='POST'
            )
            
            with urllib.request.urlopen(req, context=context, timeout=30) as response:
                body = response.read().decode('utf-8')
                if response.status == 200:
                    return self._parse_response(body)
                else:
                    return {"success": False, "error": f"HTTP {response.status}: {body[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_response(self, xml_text):
        try:
            root = ET.fromstring(xml_text)
            
            return_node = None
            for node in root.iter():
                if node.tag.endswith('return'):
                    return_node = node
                    break
            
            if return_node is not None:
                data = {}
                for child in return_node:
                    tag = child.tag.split('}')[-1]
                    data[tag] = child.text
                
                return {
                    "value": float(data.get('value', 0)),
                    "unit": data.get('unit'),
                    "valid_from": data.get('validityFrom'),
                    "valid_until": data.get('validityTo'),
                    "success": data.get('success') == 'true',
                    "id": data.get('id')
                }
            return {"success": False, "error": "Could not find return node in SOAP response"}
        except Exception as e:
            return {"success": False, "error": f"Parsing error: {e}"}

if __name__ == "__main__":
    service = TRMService()
    print(service.get_current_trm())
