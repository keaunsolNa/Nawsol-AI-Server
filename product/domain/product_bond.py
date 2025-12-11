from datetime import datetime

class ProductBond:
    def __init__(self, basDt:datetime, crno: str, bondIsurNm:str, bondIssuDt:datetime, scrsItmsKcd:str, scrsItmsKcdNm:str,
                 isinCd:str, isinCdNm:str, bondIssuFrmtNm:str, bondExprDt:datetime, bondIssuCurCd:str, bondIssuCurCdNm:str,
                 bondPymtAmt:int, bondIssuAmt:int, bondSrfcInrt:float, irtChngDcd:str, irtChngDcdNm:str, bondIntTcd:str, bondIntTcdNm:str):
        self.basDt = basDt
        self.crno = crno
        self.bondIsurNm = bondIsurNm
        self.bondIssuDt = bondIssuDt
        self.scrsItmsKcd = scrsItmsKcd
        self.scrsItmsKcdNm = scrsItmsKcdNm
        self.isinCd = isinCd
        self.isinCdNm = isinCdNm
        self.bondIssuFrmtNm = bondIssuFrmtNm
        self.bondExprDt = bondExprDt
        self.bondIssuCurCd = bondIssuCurCd
        self.bondIssuCurCdNm = bondIssuCurCdNm
        self.bondPymtAmt = bondPymtAmt
        self.bondIssuAmt = bondIssuAmt
        self.bondSrfcInrt = bondSrfcInrt
        self.irtChngDcd = irtChngDcd
        self.irtChngDcdNm = irtChngDcdNm
        self.bondIntTcd = bondIntTcd
        self.bondIntTcdNm = bondIntTcdNm