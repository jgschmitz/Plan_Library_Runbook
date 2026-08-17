| **–Application Name \| Project \| Initiative Name–** | Plan Library                                                       |
| ---------------------------------------------------- | ------------------------------------------------------------------ |
| **–Business Unit–**                                  | E&I                                                                |
| **–Tiger Fast/ Classic/ Sprint and why**<br>         | Fast - single NWL, not complex decision process (need to validate) |




| **–Why do Anything (Value Drivers)?--** |   |
| --------------------------------------- | - |

- Currently on prem and moving to Atlas on GCP in Q3
- Moving for scalability and onboarding other LOBs (primary motive)- Optum 




| <br>                                  |                                       |
| ------------------------------------- | ------------------------------------- |
| **–Timeline//Milestone Date? Why?--** | September / Prior to Open Enrollment  |

- Plan Library was the first application of USP that was designated to leverage UCP platform 
- UCP platform now able to leverage cluster-to-cluster sync connectivity 
  - Plan Library is testing 
-


|   |
| - |




| **–Application Use case –** |   |
| --------------------------- | - |

- **Plan Library** serves as an “enterprise asset” for building and managing member benefit plans. It feeds data to Cirrus and other apps across E&I. Plan library is an ecosystem of 8-9 smaller apps that each serve a specific purpose on the backend, such as plan summarization, data visualization, ideate/clone, etc.
- Internal users are benefits and configuration teams across E&I, C&S, A&I BUs. Plans of onboarding additional BUs across the organization
- Plan Library -comprised of 15 small applications that are a one-stop shop for all product and benefit administration needs
- One of the core capabilities of plan library is this validate capability
- All of the business rules, state-level rules and federal mandates  - it encompasses all these libraries 
- Market Mandate Library - 
- Metadata to organize the rules in a meaningful but they can’t search the rules - looking for a string and that’s really it
- System service as a central repo to build benefit plan information for members. Feeds data to Cirrus and other apps across E&I. 
  Quote: “Think of our app like building the plans, then sending the data out to be repurposed by other apps/teams”
- Primary users: Internal. Users are benefits and a configuration team.
  \- configure plans, business plans, federal mandates, etc
- Spread across internal E&I teams
- What does a document represent? The application's documents represent plan structures with detailed information like in-network and out-of-network services.


&#x9;

| **–Current State**  | -OVERVIEW-: Currently on MongoDB on-prem. Application needs to scale as applications onboards more businesses. Feeds data to nimbus and Cirrus. <br><br>-NCs-:<br>Being unable to effectively scale w/o impacting performance<br><br><br> |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **–Future State:—** | **Current Infrastructure**                                                                                                                                                                                                                |

- Prod
  - On-prem 3 node replica set
  - 16GB RAM
  - 4 CPUs
  - 54GB disk space used
- Non-prod environments:
  - Staging - mirror Prod
  - Dev & Test - ½ of Prod data volume and usage



**Atlas Infrastructure Requirements**

- GCP Cloud
- P1 application so no tolerance for downtime
  - App will be deployed in two regions (central and east)
- 8 second internal SLA
- Ease of migration - team will be doing a 1:1 migration, using mongosync
- Assumption: Continuous cloud backups for Prod, snapshot backups for Staging, backups off for Test and **Modernization and Scalability:** 3x data growth over 5 years, drive increased adoption of the platform

| **–Competitive Info** (who and why)--- | <br><br> |
| -------------------------------------- | -------- |
| **RCs**                                |          |

- Ability to sync data between on-prem and cloud clusters
  - Continuous? One time?
  - Cloud Migration Playbook for guidance/best practices
- **Tech Sprawl:** Managing separate systems impact performance and cost 
- **Flexible Schema:** As data needs for individual plans change over time, easy to change/update.
- **Native feature capabilities:** ability to search across mandates / rules
  - Elastic → Atlas Search
- API response time **<8 sec**
- Backend Processing **< 30 sec**
- Reduce TCO on infrastructure **20-30%**

| **–Other Key Information —** | <br>Precursors before migration:<br>Top: <br>Database strategy - Abstract Layers? <br>Enterprise Access - firewalls, ensuring enterprise can access app<br>Specific to API strategy -- not discussed |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |







| **—-----Stakeholders—--** |                                            |                                                                 |
| ------------------------- | ------------------------------------------ | --------------------------------------------------------------- |
| -Name-                    | -Role-                                     | -Notes-                                                         |
| Connor Rippley            | Head of Plan Library                       | Connor was the one to select MongoDB for Plan Library years ago |
| Jignesh Patel             | Lead Architect- Head of Migration project  | From Accenture but has been running many of the calls           |
| Rajat Bhatnagar           | Lead Engineering Manager                   | <br>                                                            |
| Saini Vinay               | <br>                                       | <br>                                                            |
| Sai Charan                | <br>                                       | <br>                                                            |
| Cherry Buchanan           | <br>                                       | <br>                                                            |





| **Still Need\*\*\*\*** | <br>Will be following up with team on search in mid september = |
| ---------------------- | --------------------------------------------------------------- |





**OTHER RELEVANT LINKS**

- LINK 1
- Etc…




**—----- INSERT DIAGRAMS/ SCREENSHOTS BELOW —-----**



Connor 

UHC Technology - part of Optum

Product and Benefits Administration suite of Tools

Not involved in claim payment

Benefits set-up and compliance and state and federal regulations 

12 teams

145 people 

Plan Library -comprised of 15 small applications that are a one-stop shop for all product and benefit administration needs

One of the core capabilities of plan library is this validate capability

All of the business rules, state-level rules and federal mandates  - it encompasses all these libraries 

Market Mandate Library - 

Metadata to organize the rules in a meaningful but they can’t search the rules - looking for a string and that’s really it

Already in MongoDB on-prem

Atlas this year or next year - 70% of data is in MongoDB 



Why Mongo?

They push teams to store data there because it’s an easy rewrite

Downstream dependencies have forced them to use SQL Server and MySQL (they currently have all 3 - Connor doesn’t like this)

Eventually wants to be 90/10 Mongo



Why Anything?

Plan Library focused on Performance as it gets more and more traction internally - pushing limits on what servers can provide 

Number crunching and data transformation - constantly setting up new servers (currently at 24 servers)

Elasticity and scale up and down - stuck and growing at 24 servers 

Performance CTO - pushing to get APIs to return a response in 8 second or less 

Backend processing below 30 seconds - lots of data transformation - rules and 

User - Config Analyst  - configuring the state of Utah - before I configure these benefits what mandates for internal rules apply to those benefit plans 

Build your own view - select the different types of rules they want to view 

Apply filter s and save view - “Utah Mandates” save on home page 

Mandates that are required 

Help the analysts look for the appropriate mandates based on what structure the product teams have submitted.

Initial set-up 

Search across all the mandates - just a rule about a co-pay - no way to find that 

Want to find “co-pay” in all of these rules and return those results to the end user

Mandates - we miss them and the regulators actually missed them

Fully insured products - filed with state regulators - send them to states where they want to offer those plan - 5-day turnaround time for why we’ve done what we’ve done and they wlll reject rules that are laws in their state - find the rules a lot quicker - speed that process up



Use Case:

Initial set-up is good 

Filing process 2nd use case - law on this and here’s the law 

Growth

3x over the next 5 years 



Future-State: 

All UHG Benefits plan administered  with this platform 

Most primary business are on the platform today

Now going after to smaller, independent benefits plans and putting their data into the tool

Why Cloud

Leadership change 

Foundational items missing - no direct interconnect between Optum and Google - Optum’s firewall is wild 

Can’t make moves until after peak season Aug-Feb) no infrastructure/code change 

Interconnect delay - hybrid connectivity 

P1 and no tolerance for downtime 

Small POC on lower environment - how it operates and what it looks like

SEARCH:

Heavy users of elastic search - costs are killing them - for another application 

20GB in prod

POC Requirements:

- Ease of migration
- 8s SLA Internally
- 30s SLA Externally 




Grant notes:

- Wants to take data to Atlas and host in GCP in such a way that there is minimum friction for the cloud engineering team
- Once data is taken to the cloud, what’s the best way to connect to on prem environments?
- Connectivity issues - does this hold true for serverless? With serverless in the cloud, you don’t have to establish network parameters
- Taking this opportunity to refactor their applications - attempting to build abstract data layers
  - Would like to get rid of legacy framework they find
- Looking towards Atlas because their team has the most experience with, they have not and will not be evaluating any other cloud solutions
- Plan library is an ecosystem of 8 or 9 different applications with different MongoDB collections
  - Behind the scenes, each separate app is performing a different function
  - Ex: Digital Benefit summary creates a pdf and gives you the summary of a specific plan
  - One application creates visualizations of plan data that are ready for the customers
  - Ideate: clones an existing plan so you can build another plan off of that
  - Consume: Plan library has to get data from upstream applications which come in from something like 20000 fields. 
    - Has to still be reformatted with business logic rules and transformed into a format that the business can use
- From a user perspective it’s all one cohesive application
- They are still in the discovery phase of their own application migration
  - Rather than a big bang approach, they plan to migrate one piece at a time and evaluate the success of that
- Target date for finishing precursor activities is ASAP
  - Everything needs to be fully wound up by Q3, engineering efforts must be done by Q2, anticipates by April that these activities will be done
  - No negative ramifications as “Our timelines will be met” They are not in a huge rush or under the gun
- Data arrives on streaming layer from up and downstream applications, they pick it up and process it for end users
- Plan library would be all the way on the left hand side of the app heat map
- Need steps at a granular level/blueprint of best practices for making the migration







**Bhavik’s Notes:**

- Plan Library stores plan structures that internal users build. The app can also ship off plan structures to downstream applications.

* 2/9 Call:
  - MDB is source collection with all raw plan structures stored
    - Transformation happens into views, and downstream platforms can consume (E&I, A&I, comm. & state)
    - APIs or Kafka streams for downstream consumption
  - Data is growing exponentially
  - Users can build, visualize, summarize, plan structures

- Consume service transforms plan structures for downstream consumption

* App is already cloud-native microservices
  - Precursor activities will refactor app probably
* “Can scale on-prem” no problem - but if all apps are moving to cloud, this move is preferred
* 8-9 apps total (low impact apps slotted to move first, EA → Atlas)








**May 15th:**

- **Current state / where are they at / UCP Pilot Update?**
- **Pain points validation and Atlas questions**
  - **P1, no downtime, HA with cloud data centers**
  - **Performance SLAs**
  - **Scale concerns/ Growth into smaller businesses**
  - **Search / GenAI**
- **Timelines re-alignment + which component is in scope for this year (of 15 apps - just Market Mandate Library) Phased approach - tied **
- **Enablement w/ some discovery**
- **Next steps - Let us know about UCP and development steps, sizing exercise for scoped app**






**July 31, 2024 **



**Owee Nicolas**

**Luke Gesior **

**Vihang Deota **

**Jignesh Patel - Accenture Lead **

**Rajat Bhatnagar- Lead of Plan Library **





Plan Library



Agenda 

-Introductions 

-Align on Plan Library 

-Understand use case, timing, where they need help 

-Do they need help with architecture scope for moving to atlas knowing that they have a bunch of microservices 



\*\*Connor Rippley



Plan Library- DBA team to help manage

16 apps



Jignesh Patel- Atlanta Google Architect for the GCP\~ accenture // initial discovery phase and migration execution work 

Rajat- MN- technical owner- legacy applications that are leveraged under United healthcare- benefit plans that go through \~ Plan Library (USP- multiple applications) – business standpoint everything together 



Plan library- application that has sub applications the left hand side of USP– once they massaged the data 20,000 fields → flows to Cirrus → 



Plan library- enterprise grade set of rules – benefits, validate, transformed all in one application

Configuration plans are filed for the government source of truth → mediation layer where there is human intervention & ID plan builder and a few others that essentially plan to library. 



Already started migrating workloads to GCP & Atlas for non-production – data right now is on prem and had to get an extract data and move the JSON files 



Migrate on prem dev & test – Q1 in January and will be for stage & production will be in January



Direct access to on prem– UCP – Luke 



This will require 





\*wants to be able to sync data between these groups; dump and restore is what they already have done; 

\*production data



Scope / Architecture? Building out the development



\*cloud modernization team– 



\*review 



**August 5th **



**Agenda**

- Plan Library to walk through their architectural diagram to understand the data flow in and out of Plan Library
- Plan Library team to walk through planned Atlas architecture – this is where we will be asking more questions around the application itself to make sure that the plan will follow best practices to support Plan Library 
- Migration Plans- Play Book 
- Key Milestones around adding different types of functionality 
- Next Steps




**Next Steps **

- Operationalization overview of Atlas & Onboarding 





Notes from August 5th call from [Carl Paulson](mailto\:carl.paulson@mongodb.com):
\- Plan Library is modernizing their 16-application ecosystem, which includes upgrading Java, Spring Boot, and modularizing applications.

\- The migration plan includes specific milestones to move dev and test instances to GCP by the end of December and complete stage and production migrations by the end of March next year.

\- Requires support from MongoDB Team to configure Atlas and guidance on using Mongo sync utility for migration.

\- A POC is planned to test Mongo sync with the dev environment to ensure data synchronization and functionality.

\- The success of the migration heavily depends on the UCP platform's connectivity.

\- The plan library application has dependencies on on-prem systems and other applications that will remain on-prem.

\- Significant refactoring work is required before the migration, including upgrading technologies and containerizing applications.

\- Feedback on the cloud migration playbook is valuable for improving its relevance and usefulness for future migrations.

\- The plan library suite relies solely on MongoDB for data storage and has critical dependencies on several other on-prem applications.

\- Detailed stats from on-prem environments are needed to recommend appropriate cluster sizes and configurations in Atlas.



8/16/24

Agenda: 

- Sizing Echo Back- [https://docs.google.com/presentation/d/11xUnMDAZLbQMYVtXpJyXY\_NJVuT\_PqwBEwvAqe3YKLU/edit#slide=id.g2ac28e29102\_0\_6](https://docs.google.com/presentation/d/11xUnMDAZLbQMYVtXpJyXY_NJVuT_PqwBEwvAqe3YKLU/edit#slide=id.g2ac28e29102_0_6) 
- Onboarding- [https://docs.google.com/presentation/d/1uA7G12cNFz6Ti4y-f\_YZBn4fkW151wpw5ivlyKedu1k/edit#slide=id.g247609ec3fb\_0\_2749](https://docs.google.com/presentation/d/1uA7G12cNFz6Ti4y-f_YZBn4fkW151wpw5ivlyKedu1k/edit#slide=id.g247609ec3fb_0_2749) 

Attendees: 



-Plan Library is critical 


















**Plan Library Search — 9/13 **



8/29 last touch base w/ al and vanguard time to discuss the cluster-cluster sync capability 



Search- onboarding call; elastic use case (sees it as very expensive) and would like to understand if they could leverage atlas vs. elastic 



Heavy users in elastic in parts of the applications; costs are killing them; wants same type of functionality 



15 micro apps– mandate management is one of the app that looks at all of the mandates… – was one of the use cases 



Mandy Chatbot- helps users build out plans & ensure that mandates are confirmed 



-what use cases are being solved by elastic at the moment?

-costs associated with full text search w/ kabana 10-15k search fees (that's where we should try to erase) & also if 

-if they are just using it for lucene it could be a full replace 





**September 13th **

What type of search functionalities are you looking to accomplish? 

What type of use cases are elastic doing today? 

Vector Search? (Semantic search) – descriptions of mandates ;; similarity search 

GenAI is more of a humanlike response 





Benefit plan for all data– save all of the plan data in MongoDB today;;; essentially 



Multiple applications with filtering criteria– business logic– gets data and does some operations on it 



Business user to ask a question give me the plan code; deductible data; semantic search 



UI- elastic instance- plan code and gives us the 



When we go to atlas; looker to potentially leverage MongoDB – but requires a whole set up 



Business user goes into plan library ; instead of going to a UI w/ filtering ; being able to ask a human – to make it easier for business owner to retrieve 



Future solution- AI solution; do more of a look up 



Business user– once they have the criteria they are looking for then; currently takes a batch system; step by step approach; improving the experience; not looking to change the workflow; no latency issue; not coming from them 



Exploring options as of now– looking to potentially move to LLM 



Benefit summary plan- 

BOT- benefit plan summary and export the PDF



Currently- spring boot java application; 



-Building it from scratch; i'm trying to configure the plan; they don’t need to go to additional tabs ;; look up and then have to configure it 

-POCs for the first chatbot identify plans to create PDFs & then help with the creation of plans 



Grabbing the data from the different sources 