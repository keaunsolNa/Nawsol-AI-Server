from config.database.session import Base
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, Integer, Float
class ProductBondORM(Base):
    __tablename__ = "product_bond"
    id = Column(Integer, primary_key=True, index=True)
    basDt = Column(DateTime, default=datetime.utcnow)       # 기준일자
    crno = Column(String(255), nullable=True)                # 법인등록번호
    bondIsurNm = Column(String(255), nullable=True)         # 채권발행인명
    bondIssuDt = Column(DateTime, default=datetime.utcnow)  # 채권발행일자
    scrsItmsKcd = Column(String(255), nullable=True)        # 유가증권종목종류코드
    scrsItmsKcdNm = Column(String(255), nullable=True)      # 유가증권종목종류코드명
    isinCd = Column(String(255), nullable=True)             # ISIN코드
    isinCdNm = Column(String(255), nullable=True)           # ISIN코드명
    bondIssuFrmtNm = Column(String(255), nullable=True)     # 채권발행형태명
    bondExprDt = Column(DateTime, default=datetime.utcnow)  # 채권만기일자
    bondIssuCurCd = Column(String(255), nullable=True)      # 채권발행통화코드
    bondIssuCurCdNm = Column(String(255), nullable=True)    # 채권발행통화코드명
    bondPymtAmt = Column(BigInteger, nullable=True)               # 채권납입금액
    bondIssuAmt = Column(BigInteger, nullable=True)               # 채권발행금액
    bondSrfcInrt = Column(Float, nullable=True)             # 채권표면이율
    irtChngDcd = Column(String(255), nullable=True)         # 금리변동구분코드
    irtChngDcdNm = Column(String(255), nullable=True)       # 금리변동구분코드명
    bondIntTcd = Column(String(255), nullable=True)         # 채권이자유형코드
    bondIntTcdNm = Column(String(255), nullable=True)       # 채권이자유형코드명

    def __repr__(self):
        return f"<ProductBondORM id={self.id}>"