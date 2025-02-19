#!/usr/bin/env python
# coding: utf-8

# # GS Quant Meets Markets: Behind the Scenes of Goldman Sachs' Equity Trading Algos, By QES
# - For any questions, feedback and assistance, please do not hesitate to email us at [gs-marquee-qes](mailto:gs-marquee-qes)
# - If you want to explore further, please visit our Quantitative Execution Services hub of research, analytics, datasets and more at the [quantitative-execution-services](https://marquee.gs.com/content/markets/products/quantitative-execution-services.html) site
# 

# # The Quantitative Execution Services group....Who Are We ?

# <img src= "images/qes_who_we_are.png">

# ## Structure of the guide:
# - The guide aims to showcase a suite of datasets, computations and optimizations that GS quants typically harness when analyzing equities baskets.
# - The range of suite of analysis shown in this notebook are being used by GS internal quants, GS trading algos and range of clients globally.
# 
# In an attempt to provide a realistic set of use-cases which utilize the offerings, we consider a Long\Short Momentum basket rebalance, which a client intends to trade in the market.
# 
# Throughout the guide, we'll attempt to analyze the basket and the market, via the following prisms:
# 
# **[Section A](#Section_A): Liquidity through the QES-Marquee prism** 
# <br>We'll utilize the GS Quant API to explore the liquidity landscape across indices, and provide further analysis across expected impact, through the lens of trade difficulty clusters. Find below API docs, corresponding to the section:
# - [API Docs: QES Single Stock Volume Forecast](https://marquee.web.gs.com/s/developer/datasets/SINGLE_STOCK_VOLUME_FORECAST_BASE)
# - [API Docs: QES Single Stock Volume Profiles](https://marquee.web.gs.com/s/developer/datasets/SINGLE_STOCK_VOLUME_PROFILE_BASE)
# - [API Docs: GS Single Stock Market Impact Estimates](https://marquee.web.gs.com/s/developer/datasets/SINGLE_STOCK_MARKET_IMPACT) and [Global Trading Cost Analysis - March 2021 example](https://marquee.gs.com/content/markets/en/2021/03/18/e750df5a-14bf-4c8a-8d57-298757450512.html)
# - [GS Equity Trade Clusters](https://marquee.web.gs.com/s/developer/datasets/EQTRADECLUSTERS) and [QES EDGE Vol. 1 | Microstructure Clustering & Trading Implications Paper](https://marquee.gs.com/content/markets/en/2020/10/28/dc0f4cf7-e6b7-4de0-97c6-76d19f7b8a25.html)
# 
# More about clustering in section A. Here's a high level visual that demonstrates the concept:
# 
# <img src= "images/clustertingImg3.png">
# 
# **[Section B](#Section_B): ETF Passive Ownership Analysis** 
# <br>Evaluation of the Passive ownership by ETF holders for our example basket
# - [API Docs: Ownership Scores (Weekly Flow)](https://marquee.gs.com/s/developer/datasets/OWNERSHIP_SCORES_WEEKLY_FLOW)
# - [API Docs: Ownership Scores (Monthly)](https://marquee.gs.com/s/developer/datasets/OWNERSHIP_SCORES_MONTHLY)
# - [QES EDGE Vol. 2 | Effect of Shift from Active to Passive](https://marquee.gs.com/content/markets/en/2020/10/28/734dc59c-b03b-4793-9f56-98ec5ebca4d8.html)
# 
# **[Section C](#Section_C): Algorithmic Portfolio EXecution - APEX**
# <br>We'll attempt to explore the basket unwind cost, using our APEX muti-period optimizer across a range of urgency\risk aversion parameters
# - [APEX - The New Frontier in Portfolio Execution - Overview](https://marquee.gs.com/content/markets/en/2021/02/16/41e547e5-24ea-4ecb-9536-6de19884a8c4.html)
# - [APEX-in-Marquee UI](https://marquee.web.gs.com/s/portfolios/create/MPGRZ9CYS372EZD1)
# - [API Docs: APEX-in-Marquee API Docs]()
# 

# ##### Disclaimers:
# ###### Indicative Terms/Pricing Levels: This material may contain indicative terms only, including but not limited to pricing levels. There is no representation that any transaction can or could have been effected at such terms or prices. Proposed terms and conditions are for discussion purposes only. Finalized terms and conditions are subject to further discussion and negotiation.
# ###### www.goldmansachs.com/disclaimer/sales-and-trading-invest-rec-disclosures.html If you are not accessing this material via Marquee ContentStream, a list of the author's investment recommendations disseminated during the preceding 12 months and the proportion of the author's recommendations that are 'buy', 'hold', 'sell' or other over the previous 12 months is available by logging into Marquee ContentStream using the link below. Alternatively, if you do not have access to Marquee ContentStream, please contact your usual GS representative who will be able to provide this information to you.
# ###### Please refer to https://marquee.gs.com/studio/ for price information of corporate equity securities.
# ###### Notice to Australian Investors: When this document is disseminated in Australia by Goldman Sachs & Co. LLC ("GSCO"), Goldman Sachs International ("GSI"), Goldman Sachs Bank Europe SE ("GSBE"), Goldman Sachs (Asia) L.L.C. ("GSALLC"), or Goldman Sachs (Singapore) Pte ("GSSP") (collectively the "GS entities"), this document, and any access to it, is intended only for a person that has first satisfied the GS entities that: 
# ###### • the person is a Sophisticated or Professional Investor for the purposes of section 708 of the Corporations Act of Australia; and 
# ###### • the person is a wholesale client for the purpose of section 761G of the Corporations Act of Australia. 
# ###### To the extent that the GS entities are providing a financial service in Australia, the GS entities are each exempt from the requirement to hold an Australian financial services licence for the financial services they provide in Australia. Each of the GS entities are regulated by a foreign regulator under foreign laws which differ from Australian laws, specifically: 
# ###### • GSCO is regulated by the US Securities and Exchange Commission under US laws;
# ###### • GSI is authorised by the Prudential Regulation Authority and regulated by the Financial Conduct Authority and the Prudential Regulation Authority, under UK laws;
# ###### • GSBE is subject to direct prudential supervision by the European Central Bank and in other respects is supervised by the German Federal Financial Supervisory Authority (Bundesanstalt für Finanzdienstleistungsaufischt, BaFin) and Deutsche Bundesbank;
# ###### • GSALLC is regulated by the Hong Kong Securities and Futures Commission under Hong Kong laws; and
# ###### • GSSP is regulated by the Monetary Authority of Singapore under Singapore laws.
# ###### Notice to Brazilian Investors
# ###### Marquee is not meant for the general public in Brazil. The services or products provided by or through Marquee, at any time, may not be offered or sold to the general public in Brazil. You have received a password granting access to Marquee exclusively due to your existing relationship with a GS business located in Brazil. The selection and engagement with any of the offered services or products through Marquee, at any time, will be carried out directly by you. Before acting to implement any chosen service or products, provided by or through Marquee you should consider, at your sole discretion, whether it is suitable for your particular circumstances and, if necessary, seek professional advice. Any steps necessary in order to implement the chosen service or product, including but not limited to remittance of funds, shall be carried out at your discretion. Accordingly, such services and products have not been and will not be publicly issued, placed, distributed, offered or negotiated in the Brazilian capital markets and, as a result, they have not been and will not be registered with the Brazilian Securities and Exchange Commission (Comissão de Valores Mobiliários), nor have they been submitted to the foregoing agency for approval. Documents relating to such services or products, as well as the information contained therein, may not be supplied to the general public in Brazil, as the offering of such services or products is not a public offering in Brazil, nor used in connection with any offer for subscription or sale of securities to the general public in Brazil.
# ###### The offer of any securities mentioned in this message may not be made to the general public in Brazil. Accordingly, any such securities have not been nor will they be registered with the Brazilian Securities and Exchange Commission (Comissão de Valores Mobiliários) nor has any offer been submitted to the foregoing agency for approval. Documents relating to the offer, as well as the information contained therein, may not be supplied to the public in Brazil, as the offer is not a public offering of securities in Brazil. These terms will apply on every access to Marquee.
# ###### Ouvidoria Goldman Sachs Brasil: 0800 727 5764 e/ou ouvidoriagoldmansachs@gs.com
# ###### Horário de funcionamento: segunda-feira à sexta-feira (exceto feriados), das 9hs às 18hs.
# ###### Ombudsman Goldman Sachs Brazil: 0800 727 5764 and / or ouvidoriagoldmansachs@gs.com
# ###### Available Weekdays (except holidays), from 9 am to 6 pm.
#  
# ###### Note to Investors in Israel: GS is not licensed to provide investment advice or investment management services under Israeli law.
# ###### Notice to Investors in Japan
# ###### Marquee is made available in Japan by Goldman Sachs Japan Co., Ltd.
# 
# ###### 本書は情報の提供を目的としております。また、売却・購入が違法となるような法域での有価証券その他の売却若しくは購入を勧めるものでもありません。ゴールドマン・サックスは本書内の取引又はストラクチャーの勧誘を行うものではございません。これらの取引又はストラクチャーは、社内及び法規制等の承認等次第で実際にはご提供できない場合がございます。
# 
# ###### <適格機関投資家限定　転売制限>
# ###### ゴールドマン・サックス証券株式会社が適格機関投資家のみを相手方として取得申込みの勧誘（取得勧誘）又は売付けの申込み若しくは買付けの申込みの勧誘(売付け勧誘等)を行う本有価証券には、適格機関投資家に譲渡する場合以外の譲渡が禁止される旨の制限が付されています。本有価証券は金融商品取引法第４条に基づく財務局に対する届出が行われておりません。なお、本告知はお客様によるご同意のもとに、電磁的に交付させていただいております。
# ###### ＜適格機関投資家用資料＞ 
# ###### 本資料は、適格機関投資家のお客さまのみを対象に作成されたものです。本資料における金融商品は適格機関投資家のお客さまのみがお取引可能であり、適格機関投資家以外のお客さまからのご注文等はお受けできませんので、ご注意ください。 商号等/ゴールドマン・サックス証券株式会社 金融商品取引業者　関東財務局長（金商）第６９号 
# ###### 加入協会/　日本証券業協会、一般社団法人金融先物取引業協会、一般社団法人第二種金融商品取引業協会 
# ###### 本書又はその添付資料に信用格付が記載されている場合、日本格付研究所（JCR）及び格付投資情報センター（R&I）による格付は、登録信用格付業者による格付（登録格付）です。その他の格付は登録格付である旨の記載がない場合は、無登録格付です。無登録格付を投資判断に利用する前に、「無登録格付に関する説明書」（http://www.goldmansachs.com/disclaimer/ratings.html）を十分にお読みください。 
# ###### If any credit ratings are contained in this material or any attachments, those that have been issued by Japan Credit Rating Agency, Ltd. (JCR) or Rating and Investment Information, Inc. (R&I) are credit ratings that have been issued by a credit rating agency registered in Japan (registered credit ratings). Other credit ratings are unregistered unless denoted as being registered. Before using unregistered credit ratings to make investment decisions, please carefully read "Explanation Regarding Unregistered Credit Ratings" (http://www.goldmansachs.com/disclaimer/ratings.html).
# ###### Notice to Mexican Investors: Information contained herein is not meant for the general public in Mexico. The services or products provided by or through Goldman Sachs Mexico, Casa de Bolsa, S.A. de C.V. (GS Mexico) may not be offered or sold to the general public in Mexico. You have received information herein exclusively due to your existing relationship with a GS Mexico or any other Goldman Sachs business. The selection and engagement with any of the offered services or products through GS Mexico will be carried out directly by you at your own risk. Before acting to implement any chosen service or product provided by or through GS Mexico you should consider, at your sole discretion, whether it is suitable for your particular circumstances and, if necessary, seek professional advice. Information contained herein related to GS Mexico services or products, as well as any other information, shall not be considered as a product coming from research, nor it contains any recommendation to invest, not to invest, hold or sell any security and may not be supplied to the general public in Mexico.
# ###### Notice to New Zealand Investors: When this document is disseminated in New Zealand by Goldman Sachs & Co. LLC ("GSCO") , Goldman Sachs International ("GSI"), Goldman Sachs Bank Europe SE ("GSBE"), Goldman Sachs (Asia) L.L.C. ("GSALLC") or Goldman Sachs (Singapore) Pte ("GSSP") (collectively the "GS entities"), this document, and any access to it, is intended only for a person that has first satisfied; the GS entities that the person is someone: 
# ###### (i) who is an investment business within the meaning of clause 37 of Schedule 1 of the Financial Markets Conduct Act 2013 (New Zealand) (the "FMC Act");
# ###### (ii) who meets the investment activity criteria specified in clause 38 of Schedule 1 of the FMC Act;
# ###### (iii) who is large within the meaning of clause 39 of Schedule 1 of the FMC Act; or
# ###### (iv) is a government agency within the meaning of clause 40 of Schedule 1 of the FMC Act. 
# ###### No offer to acquire the interests is being made to you in this document. Any offer will only be made in circumstances where disclosure is not required under the Financial Markets Conducts Act 2013 or the Financial Markets Conduct Regulations 2014.
# ###### Notice to Swiss Investors: This is marketing material for financial instruments or services. The information contained in this material is for general informational purposes only and does not constitute an offer, solicitation, invitation or recommendation to buy or sell any financial instruments or to provide any investment advice or service of any kind.
# ###### THE INFORMATION CONTAINED IN THIS DOCUMENT DOES NOT CONSITUTE, AND IS NOT INTENDED TO CONSTITUTE, A PUBLIC OFFER OF SECURITIES IN THE UNITED ARAB EMIRATES IN ACCORDANCE WITH THE COMMERCIAL COMPANIES LAW (FEDERAL LAW NO. 2 OF 2015), ESCA BOARD OF DIRECTORS' DECISION NO. (9/R.M.) OF 2016, ESCA CHAIRMAN DECISION NO 3/R.M. OF 2017 CONCERNING PROMOTING AND INTRODUCING REGULATIONS OR OTHERWISE UNDER THE LAWS OF THE UNITED ARAB EMIRATES. ACCORDINGLY, THE INTERESTS IN THE SECURITIES MAY NOT BE OFFERED TO THE PUBLIC IN THE UAE (INCLUDING THE DUBAI INTERNATIONAL FINANCIAL CENTRE AND THE ABU DHABI GLOBAL MARKET). THIS DOCUMENT HAS NOT BEEN APPROVED BY, OR FILED WITH THE CENTRAL BANK OF THE UNITED ARAB EMIRATES, THE SECURITIES AND COMMODITIES AUTHORITY, THE DUBAI FINANCIAL SERVICES AUTHORITY, THE FINANCIAL SERVICES REGULATORY AUTHORITY OR ANY OTHER RELEVANT LICENSING AUTHORITIES IN THE UNITED ARAB EMIRATES. IF YOU DO NOT UNDERSTAND THE CONTENTS OF THIS DOCUMENT, YOU SHOULD CONSULT WITH A FINANCIAL ADVISOR. THIS DOCUMENT IS PROVIDED TO THE RECIPIENT ONLY AND SHOULD NOT BE PROVIDED TO OR RELIED ON BY ANY OTHER PERSON.
