from config import config_input
from utils import sheet_uploader
from utils.bypass.cloudflare import CloudflareBypasser
from utils import helper




async def extract_full_details(context, urls , percentages):
    
    # Define fixed column order 
    fixed_keys = ["company_name", "url"]
    
    # Add blank columns if configured
    if isinstance(config_input.leave_blank_colls, int) and config_input.leave_blank_colls > 0:
        fixed_keys.extend([f"blank_{i+1}" for i in range(config_input.leave_blank_colls)])
    
    # Add remaining keys in fixed order
    fixed_keys.extend([
        "matching_per",
        "job_title",
        "salary",
        "job_other_details",
        "benefits",
        "full_description"
    ])
    
    easy_applies = []
    cs_applies = []
    c_applies  = []
    unclassified_jobs = []

    tab2_page = await context.new_page()
    
    for p_index , url in enumerate(urls):
        full_url = f"https://indeed.com{url}"

        try:
            # await asyncio.sleep(random.randint(1,3))
            try:
                await tab2_page.goto(full_url, wait_until="load", timeout=30000)
            except Exception as e:
                try:
                    await tab2_page.reload()
                    await tab2_page.goto(full_url, wait_until="load", timeout=30000)
                except Exception as e:
                    print(e)

                

            # await asyncio.sleep(random.randint(1,3))
            await helper.simulate_human_behavior(tab2_page)
           
            # Bypass Cloudflare if present 
            try:
                cf_bypasser = CloudflareBypasser(tab2_page)
                await cf_bypasser.detect_and_bypass()
            except Exception as e:
                print(e)
        except Exception as e:
            print(f"🚫 Failed to load {full_url}: {str(e)}")
            continue
        
        # Initialize job_data with all keys (ensures no missing columns)
        job_data = {key: "" for key in fixed_keys}
        job_data.update({
            "url": full_url,
            "matching_per": percentages[p_index]
        })

        # Skip when there are word about clearance
        try:
            content = await tab2_page.content()
            if any(keyword in content for keyword in ["clearance", "government", "cyber"]):
                continue
        except Exception as e:
            print(e)
        
        # Extract job details
        try:
            company_el = (await tab2_page.query_selector('[data-testid="company-name"]') or 
              await tab2_page.query_selector('[data-testid="inlineHeader-companyName"]'))
            if company_el:
                job_data["company_name"] = (await company_el.inner_text()).strip()
            else:
                continue
                print(f"⚠ Failed to extract company name")

            
            # Job title
            title_el = await tab2_page.query_selector('[data-testid="jobsearch-JobInfoHeader-title"] span')
            if title_el:
                job_data["job_title"] = (await title_el.inner_text()).strip()
            else:
                continue
                print(f"⚠ Failed to extract title")
                
            
            # Salary title
            salary_el = await tab2_page.query_selector('#salaryInfoAndJobType')
            if salary_el:
                job_data["salary"] = (await salary_el.inner_text()).strip()
            else:
                # print(f"⚠ Failed to extract salary")
                pass
            
            # job_other_details
            try:
                el = await tab2_page.query_selector('[data-testid="jobsearch-CompanyInfoContainer"]')
                if el:
                    job_data["job_other_details"] = (await el.inner_text()).strip()
            except Exception as e:
                print("job_other_details info error:", e)
            
            # Benefits
            benefits_el = await tab2_page.query_selector('[data-testid="benefits-test"]')
            if benefits_el:
                job_data["benefits"] = (await benefits_el.inner_text()).strip()
            else:
                # print(f"⚠ Failed to extract benefits section")
                pass
            
            # Description
            desc_el = await tab2_page.query_selector('#jobDescriptionText')
            if desc_el:
                job_data["full_description"] = (await desc_el.inner_text()).strip()
            else:
                print(f"⚠ Failed to extract description")
        except Exception as e:
            print(f"⚠ Partial data for {full_url}: {str(e)}")

        # Build row in FIXED order
        row = [job_data[key] for key in fixed_keys]
        
        # Check application type
        try:
            if await tab2_page.query_selector(':has-text("This job has expired on Indeed")'):
                print(f"⏳ Expired job: {job_data['company_name']}")
                continue
                
            is_web_apply = bool(await tab2_page.query_selector(':has-text("Apply on company site")'))
            
            if job_data["company_name"] in getattr(config_input, 'confirmation_companies', []):
                c_applies.append(row)
                print(f"🔔 Confirmation: {job_data['company_name']}")
            elif is_web_apply:
                cs_applies.append(row)
                print(f"🌐 Company Site: {job_data['company_name']}")
            else:
                easy_applies.append(row)
                print(f"⚡ Easy Apply: {job_data['company_name']}")
                
        except Exception as e:
            unclassified_jobs.append(full_url)
            print(f"❓ Unclassified job: {full_url} - {str(e)}")

    await tab2_page.close()

    # Save to  excel jobs file
    await sheet_uploader.jobs_append_to_csv(easy_applies, cs_applies, c_applies)

    

