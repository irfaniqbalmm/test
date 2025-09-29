import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from utils.logger import logger

# Function to prettify the XML
def prettify_xml(elem):
    """
    Method name: prettify_xml
    Description: Return a pretty-printed XML string for the Element.
    Parameters:
        elem : element to be prettified
    Returns:
        prettified element
    """
    logger.info("Prettifying XML file.")
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

# Function to convert the JSON to XML
def json_to_xml(json_file, output_xml):
    """
    Method name: json_to_xml
    Description: Convert the json file into xml format file
    Parameters:
        json_file : json file to be converted
        output_xml : xml file generated
    Returns:
        None
    """
    with open(json_file, 'r') as f:
        data = json.load(f)

    logger.info("Initialising test suites.")
    # Create the root element <testsuites>
    testsuites = ET.Element("testsuites")

    # Create a testsuite element for BVT
    logger.info("Adding BVT testsuite.")
    bvt_testsuite = ET.SubElement(testsuites, "testsuite")
    bvt_testsuite.set("name", "ContentPattern_BVT_tests")
    length = len(data)

    for key, status in data.items():
        if status == "None" :
            length = length - 1
            continue
        if key in ['egress','liberty_version','java_build','java_version','fips'] :
            length = length - 1
            continue
        if key == 'OC_Automations' and status == 'Not executed':
            length = length - 1
            continue
        if key == 'MVT' :
            continue

        testcase = ET.SubElement(bvt_testsuite, "testcase")
        testcase.set("classname", key)
        testcase.set("name", key)
        testcase.set("time", "0.123")  
        
        if "PASSED" in status :
            continue 
        elif "FAILED" in  status :
            failure = ET.SubElement(testcase, "failure")
        elif status == "Not executed":
            skipped = ET.SubElement(testcase, "skipped")

    # Count the number of tests in BVT
    bvt_testsuite.set("tests", str(length))
    failures = sum(1 for test in data.values() if "FAILED" in test)
    bvt_testsuite.set("failures", str(failures))
    bvt_testsuite.set("errors", "0") 
    skipped = sum(1 for test in data.values() if test == "Not executed")
    bvt_testsuite.set("skipped", str(skipped))
    bvt_testsuite.set("time", "0.123")  # Static time for example purposes

    #MVT
    logger.info("Adding MVT testsuite.")
    if "MVT" in data :
        mvt_status = data["MVT"]
        mvt_testsuite = ET.SubElement(testsuites, "testsuite")
        mvt_testsuite.set("name", "ContentPattern_MVT_tests")
        length = 1
        mvt_testcase = ET.SubElement(mvt_testsuite, "testcase")
        mvt_testcase.set("classname", "MVT")
        mvt_testcase.set("name", "MVT")
        mvt_testcase.set("time", "0.123")  

        if "FAILED" in mvt_status:
            ET.SubElement(mvt_testcase, "failure")
        elif mvt_status == "Not executed":
            ET.SubElement(mvt_testcase, "skipped")

        # Count the number of tests
        mvt_testsuite.set("tests", str(length))
        failures = sum(1 for test in data.values() if "FAILED" in test)
        mvt_testsuite.set("failures", str(failures))
        mvt_testsuite.set("errors", "0") 
        skipped = sum(1 for test in data.values() if test == "Not executed")
        mvt_testsuite.set("skipped", str(skipped))
        mvt_testsuite.set("time", "0.123")  

    # Get the prettified XML string
    pretty_xml = prettify_xml(testsuites)

    with open(output_xml, 'w') as f:
        f.write(pretty_xml)

def generate_xml_report(filename) :
    """
    Method name: generate_xml_report
    Description: Fucntion call to generate the xml report
    Parameters:
        filename : name of xml file generated
    Returns:
        None
    """

    logger.info("==========================================Starting creation of BVT XML report==========================================")
    json_file = os.getcwd() + "/reports/generated_reports/bvt_status.json"
    output_xml = os.getcwd() + f"/reports/generated_reports/{filename}.xml"
    json_to_xml(json_file, output_xml)
    logger.info(f"XML report generated: {output_xml}")
    logger.info("==========================================Completed creation of BVT XML report==========================================\n\n")

if __name__ == "__main__" :
    generate_xml_report("bvt_admin_xml_report")
