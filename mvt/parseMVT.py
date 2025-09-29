import re
from abc import ABC, abstractmethod

import pandas as pd
from pandas.io.formats.style import Styler
import pdfkit
from bs4 import BeautifulSoup

from mvt.verify_mvt_versions import VerifyMvtVersion

class Component(ABC):
    """
    Class name  :   Component
    Description :   Acts as an interface for component parsing.
                    Different components require different parsing.
    """

    def __init__(self):
        self._component_name = self.get_component_name()

    @abstractmethod
    def get_component_name(self, content=None) -> str:
        """
        Method name :   get_component_name
        Description :   Returns the name of the component whose content is to be parsed
        Parameters  :   None
        Returns     :   String
        """
        raise NotImplementedError

    @abstractmethod
    def get_version_txt_precursor(self, ) -> str:
        """
        Method name :   get_version_txt_precursor
        Description :   Returns the string which immediately precedes the version in the version.txt file, used in parse_version.
        Parameters  :   None
        Returns     :   String
        """
        raise NotImplementedError

    def parse_version(self, content) -> str:
        """
        Method name :   get_version_txt_precursor
        Description :   Returns the version number of the component
                        Assumes version can be parsed after `csi-`, otherwise, make sure to override
        Parameters  :   
            content : Component details
        Returns     :   String
        """
        assert isinstance(content, str)
        precursor_string = self.get_version_txt_precursor()
        precursor_index = content.find(precursor_string)
        if precursor_index == -1:
            return 'N/A'
        elif "ICCSAP" in content:
            version_number = re.search(r'^.*?(?=,)', content[precursor_index + len(precursor_string):])
            if version_number.group(0) is not None:
                return version_number.group(0)
        else:
            version_number = re.search(r'(\S+)', content[precursor_index + len(precursor_string):])
            if version_number.group(0) is not None:
                return version_number.group(0)

    def parse_websphere_version(self, content) -> str:
        """
        Method name :   parse_websphere_version
        Description :   Returns the websphere version of the component
        Parameters  :   
            content : Component details
        Returns     :   String
        """
        # TODO: Implement
        precursor_string = 'WebSphere Application Server '
        precursor_index = content.find(precursor_string)
        if precursor_index == -1:
            return 'N/A'
        else:
            retval = re.search(r'(\d+\.?)+', content[precursor_index + len(precursor_string):])
            if retval.group(0) is not None:
                return retval.group(0)
        # return f'Test websphere: {self._component_name}'

    @staticmethod
    def parse_java_version(content) -> str:
        """
        Method name :   parse_java_version
        Description :   Returns the java version of the component
        Parameters  :   
            content : Component details
        Returns     :   String
        """
        # TODO: Implement
        precursor_string = ['IBM Semeru Runtime Certified Edition',
                            'Java(TM) SE Runtime Environment']
        # Loop through all possible precursor strings
        for precursor in precursor_string:
            precursor_index = content.find(precursor)
            if precursor_index != -1:
                version_number = re.search(r'(\d+\.?)+', content[precursor_index + len(precursor):])
                if version_number.group(0) is not None:
                    return version_number.group(0)
        return 'N/A'
    
    def parse_ubi_version(self, content) -> str:
        """
        Method name :   parse_ubi_version
        Description :   Returns the UBI version of the component
        Parameters  :   
            content : Component details
        Returns     :   String
        """
        precursor_string = 'Red Hat Enterprise Linux release'
        precursor_index = content.find(precursor_string)
        if precursor_index == -1:
            return 'N/A'
        else:
            retval = re.search(r'(\d+\.?)+', content[precursor_index + len(precursor_string):])
            if retval.group(0) is not None:
                return retval.group(0)

    def parse_licenses(self, content) -> str:
        """
        Method name :   parse_licenses
        Description :   Returns the licences  of the component
        Parameters  :   
            content : Component details
        Returns     :   String
        """
        # TODO: Implement
        license_matches = re.findall(r'LI([a-zA-Z_.]*)', content)
        retval = ''
        for matchObject in license_matches:
            retval += 'LI' + matchObject + ';'
        retval = retval.rstrip(';')
        return retval
        # return 'Test licenses'

    def parse_swidtags(self, content) -> str:
        """
        Method name :   parse_swidtags
        Description :   Returns the swidtags of the component
        Parameters  :   
            content : Component details
        Returns     :   String
        """
        # TODO: Implement
        if content.find('No swidtags found') != -1 or 'No such file or directory' in content:
            return 'N/A'
        return 'Swidtags Found'

    def parse_annotations(self, content) -> str:
        """
        Method name :   parse_annotations
        Description :   Returns the annotations of the component
        Parameters  :   
            content : Component details
        Returns     :   String
        """
        # TODO: Implement
        retval = ''
        version = re.search(r'productVersion: (\d+\.?)+', content)
        if version is not None:
            retval += version.group(0) + ';\n'
        productID = re.search(r'productID: .*', content)
        if productID is not None:
            retval += productID.group(0) + ';\n'
        productName = re.search(r'productName: .*', content)
        if productName is not None :
            retval += productName.group(0)
        if version is None and productID is None and productName is None :
            return 'No Annotations Found'
        return retval

# TODO: Implement abstract methods for every sub-class of Component
class Operator(Component):
    def get_component_name(self, content=None) -> str:
        return 'Operator'

    def get_version_txt_precursor(self, ) -> str:
        return ''

    def parse_version(self, content) -> str:
        """
        Method name : parse_version
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description : Parses the version, builds, and images from the given content.
        Parameters:
            content (str): The content to parse.
        Returns:
            str: A string containing the version, builds, and images.
        Raises:
            AssertionError: If the content is not a string.
        """
        assert isinstance(content, str)
        version = ''
        version_match =  re.search(r"(?<=Version:\s)\d+\.\d+\.\d+",content)
        if version_match : 
            version = version_match.group()
        builds = re.findall(r'From.*', content)
        images = re.findall(r'CP4BA.*', content)
        retval = ''
        if len(builds) == 0 and len(images) == 0:
            return 'N/A'
        else:
            retval += f"Version : {version}\n"
            for build in builds:
                retval += build + '\n'
            for image in images :
                retval += image + '\n'
            return retval[:-1]
        

class contentOperator(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Operator'

    def get_version_txt_precursor(self, ) -> str:
        return ''

    def parse_version(self, content) -> str:
        assert isinstance(content, str)
        builds = re.findall(r'From.*', content)
        retval = ''
        if len(builds) == 0:
            return 'N/A'
        else:
            for build in builds:
                retval += build + '\n'
            return retval[:-1]


class dpeOperator(Component):
    def get_component_name(self, content=None) -> str:
        return 'DPE Operator'

    def get_version_txt_precursor(self, ) -> str:
        return ''

    def parse_version(self, content) -> str:
        assert isinstance(content, str)
        builds = re.findall(r'[\S\s]', content)
        retval = content
        if len(builds) == 0:
            return 'N/A'
        else:
            return retval

class CPFS(Component):
    def get_component_name(self, content=None) -> str:
        return 'CPFS'

    def get_version_txt_precursor(self, ) -> str:
        return ''

class Flink(Component):
    def get_component_name(self, content=None) -> str:
        return 'Flink'

    def get_version_txt_precursor(self, ) -> str:
        return ''

class Kafka(Component):
    def get_component_name(self, content=None) -> str:
        return 'Kafka'

    def get_version_txt_precursor(self, ) -> str:
        return ''
    
class OS(Component):
    def get_component_name(self, content=None) -> str:
        return 'OS'

    def get_version_txt_precursor(self, ) -> str:
        return ''
    
class ZEN(Component):
    def get_component_name(self, content=None) -> str:
        return 'Zen'

    def get_version_txt_precursor(self, ) -> str:
        return 'latest_version:'

class CMIS(Component):
    def get_component_name(self, content=None) -> str:
        return 'CMIS'

    def get_version_txt_precursor(self, ) -> str:
        return 'build cmis:'


class CPE(Component):
    def get_component_name(self, content=None) -> str:
        return 'CPE'

    def get_version_txt_precursor(self, ) -> str:
        return 'CPE container'


class CSS(Component):
    def get_component_name(self, content=None) -> str:
        return 'CSS'

    def get_version_txt_precursor(self, ) -> str:
        return 'IBM Content Search Services, build css:'


class ES(Component):
    def get_component_name(self, content=None) -> str:
        return 'ES'

    def get_version_txt_precursor(self, ) -> str:
        return 'External Share, build:'


class GraphQL(Component):
    def get_component_name(self, content=None) -> str:
        return 'GraphQL'

    def get_version_txt_precursor(self, ) -> str:
        return 'container version:'


class Navigator(Component):
    def get_component_name(self, content=None) -> str:
        return 'Navigator'

    def get_version_txt_precursor(self, ) -> str:
        return 'build navigator:'


class TM(Component):
    def get_component_name(self, content=None) -> str:
        return 'TM'

    def get_version_txt_precursor(self, ) -> str:
        return 'Task Manager, build:'
    
class IER(Component):
    def get_component_name(self, content=None) -> str:
        return 'IER'

    def get_version_txt_precursor(self, ) -> str:
        return 'IER, build:'

class ICCSAP(Component):
    def get_component_name(self, content=None) -> str:
        return 'ICCSAP'

    def get_version_txt_precursor(self, ) -> str:
        return 'ICCSAP'

class BAI(Component):
    def get_component_name(self, content=None) -> str:
        return 'BAI'

    def get_version_txt_precursor(self, ) -> str:
        return ' '
    
    def parse_version(self, content) -> str:
        assert isinstance(content, str)
        images = re.findall(r'Business.*', content)
        retval = ''
        if len(images) == 0:
            return 'N/A'
        else:
            for image in images :
                retval += image + '\n'
            return retval[:-1]

class BAStudio(Component):
    def get_component_name(self, content=None) -> str:
        return 'BAStudio'

    def get_version_txt_precursor(self, ) -> str:
        return 'ba-studio:'

class AE(Component):
    def get_component_name(self, content=None) -> str:
        return 'AE - Workspace & PBK'
    def get_version_txt_precursor(self, ) -> str:
        return ''
    def parse_version(self, content) -> str:
        assert isinstance(content, str)
        builds = re.findall(r'[\S\s]', content)
        retval = content
        if len(builds) == 0:
            return 'N/A'
        else:
            return retval
          
class CDRA(Component):
    def get_component_name(self, content=None) -> str:
        return 'CDRA'

    def get_version_txt_precursor(self, ) -> str:
        return 'container version:'


class CDS(Component):
    def get_component_name(self, content=None) -> str:
        return 'CDS'

    def get_version_txt_precursor(self, ) -> str:
        return 'container version:'


class CPDS(Component):
    def get_component_name(self, content=None) -> str:
        return 'CPDS'

    def get_version_txt_precursor(self, ) -> str:
        return 'container version:'


class GitGateway(Component):
    def get_component_name(self, content=None) -> str:
        return 'Git Gateway'

    def get_version_txt_precursor(self, ) -> str:
        return 'version'

    def parse_version(self, content) -> str:
        assert isinstance(content, str)
        precursor_string = self.get_version_txt_precursor()
        precursor_index = content.find(precursor_string)
        if precursor_index == -1:
            return 'N/A'
        else:
            version_number = re.search(r'(\d+\.?)+', content[precursor_index + len(precursor_string):])
            if version_number.group(0) is not None:
                return version_number.group(0)


class Mongo(Component):
    def get_component_name(self, content=None) -> str:
        return 'Mongo'

    def get_version_txt_precursor(self, ) -> str:
        return 'db version'


class spbackend(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Backend'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)


class classifyprocess(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Classify process classify'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)

class deepLearning(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Deep learning'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)


class webhook(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Webhook'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)


class rabbitmqHa(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Rabbitmq-HA'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)


class ocrExtraction(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - OCR extraction'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)


class postProcessing(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Postprocessing'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)


class processingExtraction(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Processing extraction'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)


class setup(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Setup'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)


class naturalLanguageExtractor(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Natural language extractor'

    def get_version_txt_precursor(self, ) -> str:
        return 'dba-security-harden:'

    def parse_version(self, content) -> str:
        return re.search(r"{(.)(.+?)}", content).group(0)


class ViewOne(Component):
    def get_component_name(self, content=None) -> str:
        return 'ViewOne'

    def get_version_txt_precursor(self, ) -> str:
        return 'ViewOne zip version:'


class Celery(Component):
    def get_component_name(self, content=None) -> str:
        return 'Content Analyzer - Celery'

    def get_version_txt_precursor(self, ) -> str:
        return ''

    def parse_version(self, content) -> str:
        return re.search(r'Celery(\S+)', content).group(0)


class Gitea(Component):
    def get_component_name(self, content=None) -> str:
        return 'Gitea'

    def get_version_txt_precursor(self, ) -> str:
        return 'Gitea version'


class ComponentHandler:
    """
    Holds component strings, split by sections (version.txt, Java Version etc.)
    """
    # The sections of the component that are to be parsed, in order of appearance in content.
    _sections = ['Component', 'version.txt', 'Liberty Version', 'Java Version', 'UBI Version', 'Licenses', 'Swidtags', 'Annotations']

    # Map Component tag to its class e.g. content-cmis-deploy -> CMIS
    _classes = {'operator': Operator, 'ibm-cp4a-operator': Operator, 'contentOperator': contentOperator, 'dpeOperator': dpeOperator,
                'cpfs':CPFS, 'flink': Flink, 'kafka': Kafka, 'elasticsearch': OS, 'opensearch': OS, 'zen':ZEN, 
                'cmis': CMIS, 'cpe': CPE, 'css': CSS, 'es': ES, 'graphql': GraphQL, 'navigator': Navigator, 'tm': TM,
                'ier': IER, 'iccsap': ICCSAP, 'bai': BAI, 'bastudio': BAStudio, 'cdra': CDRA, 'cds': CDS, 'cpds': CPDS,
                'gitea': Gitea, 'classifyprocess': classifyprocess, 'deep': deepLearning, 'webhook': webhook,
                'rabbitmq': rabbitmqHa, 'spbackend': spbackend, 'viewone': ViewOne, 'celery': Celery, 'gitgateway': GitGateway, 'mongo': Mongo,
                'ocr': ocrExtraction, 'postprocessing': postProcessing, 'processing': processingExtraction,
                'setup': setup,'natural': naturalLanguageExtractor, 'engine': AE}

    def __init__(self, content: str):
        """
        Creates component objects and splits sections of components
        :param content: String output of automated MVT
        """
        assert isinstance(content, str)
        self._content = content

        # Maps _sections to its respective content
        self._section_content = self._split_sections()

        self._component_name = self._find_component_name()

        self._the_component = self._get_component()

        # Bind all method calls from the component to the section
        parse_methods = [self._the_component.get_component_name, self._the_component.parse_version,
                         self._the_component.parse_websphere_version, self._the_component.parse_java_version,
                         self._the_component.parse_ubi_version, self._the_component.parse_licenses, 
                         self._the_component.parse_swidtags, self._the_component.parse_annotations]
        self._to_run = dict(zip(self._sections, parse_methods))

        self._parsed = self._parse_all()

    def _split_sections(self) -> dict:
        """
        Splits the component content into sections
        """
        content = dict()
        for i in range(len(self._sections)):
            # Match between sections
            start = self._sections[i]
            if i == len(self._sections) - 1:
                match = re.search(f'(?<={start}:)[\\s\\S]*', self._content)
            else:
                end = self._sections[i + 1]
                match = re.search(f'(?<={start}:)[\\s\\S]*?(?={end})', self._content)
            content[start] = match.group(0).lstrip('\n')
        return content

    def _find_component_name(self) -> str:
        """
        Grabs the component name from the "Component" section.
        # Assume content-{componentName}-deploy or icp4adeploy-{componentName}-deploy
        """
        if 'ibm-content-operator' in self._section_content['Component'] or \
                'ibm-cp4a-operator' in self._section_content['Component']:
            return 'operator'
        elif 'ibm-insights-engine-operator' in self._section_content['Component']:
            return 'bai'
        elif 'ibm-common-service-operator' in self._section_content['Component']:
            return 'cpfs'
        elif 'flink' in self._section_content['Component']:
            return 'flink'
        elif 'kafka' in self._section_content['Component']:
            return 'kafka'
        elif 'elasticsearch' in self._section_content['Component']:
            return 'elasticsearch'
        elif 'opensearch' in self._section_content['Component']:
            return 'opensearch'
        elif 'ibm-cp4a-content-operator' in self._section_content['Component']:
            return 'contentOperator'
        elif 'ibm-cp4a-dpe-operator' in self._section_content['Component']:
            return 'dpeOperator'
        elif 'bastudio' in self._section_content['Component']:
            return 'bastudio'
        elif 'ibm-dba-aca-prod' in self._section_content['Component']:
            return 'celery'
        return self._section_content['Component'].split('-')[1].strip()

    def get_component_name(self) -> str:
        """
        Returns the component name
        """
        return self._component_name

    def _get_component(self) -> Component:
        """
        Returns the Component class based on component name from self._classes
        :return: A Component sub-class
        """
        if comp := self._classes.get(self._component_name):
            return comp()
        raise NotImplementedError(f'No class implemented for {self._component_name}. Check that the class is '
                                  f'included in self._classes')

    def _parse_all(self) -> dict:
        """
        Uses Component object to parse all sections
        :return: A dictionary mapping the section name to the parsed content
        """
        parsed = dict()
        for sect, call in self._to_run.items():
            parsed[sect] = call(self._section_content[sect])
        return parsed

    def get_parsed(self) -> pd.Series:
        """
        Returns a series with all the sections with its parsed data
        :return: pd.Series
        """
        return pd.Series(self._parsed)


def split_components(content: str) -> list:
    """
    Splits the content string into individual component's strings
    :param content: A string of the entire MVT text file
    :return: A list of strings, separated by component
    """
    return re.findall('(?=Component:)[\\s\\S]*?(?<=--------)', content)


def content2df(content: str) -> pd.DataFrame:
    
    """
    Converts content from MVT results to a dataframe highlighting desired data
    :param content: A string of the entire MVT text file
    :return: A dataframe with desired data
    """
    component_content = split_components(content)
    all_components = [ComponentHandler(comp) for comp in component_content]
    return pd.DataFrame([c.get_parsed() for c in all_components])

def create_div(soup: BeautifulSoup, text: str) -> None:
    """
    Method name :   create_div
    Description :   Creates a bs4 div object with given text
    Parameters  : 
        soup: The BeautifulSoup object to add div
        text: The data to be loaded into the div
    Returns     :   None
    """
    tag = soup.new_tag('div')
    tag.string = text
    soup.append(tag)


def style_df(df: pd.DataFrame) -> Styler:
    """
    Method name :   style_df
    Description :   Adds CSS styles the dataframe
    Parameters  : 
        df      :   The dataframe to be styled 
    Returns     :   Styled dataframe
    """
    headers = {
        'selector': 'th',
        'props': 'font-style: italic; font-weight: bold; background-color: lightgray'
    }
    border = {
        'selector': 'th, td',
        'props': 'border: 1px solid'
    }
    table_border = {
        'selector': '',  # empty to choose table itself
        'props': 'border: 1px solid'
    }
    caption = {
        'selector': 'caption',
        'props': 'font-weight: bolder'
    }

    # Apply styles
    styles = [headers, border, table_border, caption]
    return df.style.hide().set_caption('MVT Results').set_table_styles(styles)


def list2html(lst: list, ordered: bool = True) -> str:
    """
    Method name :   list2html
    Description :   Changes a list of strings into an HTML list string.
    Parameters  : 
        lst     :   The list of strings to change to HTML
        ordered :   Where the list should be ordered or unordered in HTML
    Returns     :   The list as a raw HTML string
    """
    # Open list
    html = '<ol' if ordered else '<ul'
    # Remove margin
    html += " style='margin: 0'>"
    # Fill list
    for el in lst:
        html += '<li>' + el + '</li>'
    # Close list
    html += '</ol>' if ordered else '</ul>'
    return html


def df2pdf(product: str, version: str, a_type: str, run_date: str, df: pd.DataFrame, gen_report_path: str, project_namespace: list, deployment_type:str, cluster: str, html: bool = False) -> None:
    """
    Method name :   df2pdf
    Description :   Creates a pdf structured as
    Parameters  : 
        version :   Deployment Version
        a_type  :   Deployment Type (CONTENT or CP4BA)
        run_date:   Run Date
        df      :   MVT Results with Selected Components
        project_namespace: Namespace of the Project
        html    :   Outputs file to html as well as pdf
    Returns     :   None
    """
    if len(project_namespace) == 2:
        report_namespace = project_namespace[1]
    else:
        report_namespace = project_namespace[0]
    fn = f'{gen_report_path}/MVT_{product.upper()}_{report_namespace}_{deployment_type}_{cluster}_{run_date}'
    styler = style_df(df)
    table_str = styler.to_html()
    soup = BeautifulSoup()
    components = list2html(list(df['Component']), ordered=False)

    #Add Summary of MVT 
    verify_mvt = VerifyMvtVersion(product)
    mvt_summary = verify_mvt.verification()
    soup.append(BeautifulSoup(mvt_summary, "html.parser"))

    # Add headers
    divs = [f'Deployment Version: {version}', f'Deployment Type: {a_type}', f'Selected Components:']
    for div in divs:
        create_div(soup, div)

    # Add components list
    components_html = BeautifulSoup(components, 'html.parser')
    soup.append(components_html)

    # Add more headers
    divs2 = [f'Run Date: {run_date}', f'Project Namespace: {project_namespace}']
    for div in divs2:
        create_div(soup, div)

    if product.upper() in ['CP4BA', 'CONTENT']:
        note = "<br><br>*************************************************************************************************<br>Please note that <b>Kafka, IER & ICCSAP</b> versions are not compared automatically due to un-availability of their reference.<br>*************************************************************************************************<br><br>"
    elif product.upper() == "BAIS":
        note = "<br><br>*************************************************************************************************<br>Please note that <b>Kafka</b> version is not compared automatically due to un-availability of it's reference.<br>*************************************************************************************************<br><br>"
    elif product.upper() == "ADP":
        note = "<br><br>*************************************************************************************************<br>Please note that <b>BAStudio, AE, Kafka</b> version is not compared automatically due to un-availability of it's reference.<br>*************************************************************************************************<br><br>"
    
    soup.append(BeautifulSoup(note, "html.parser"))
    # Combine headers with table
    output = str(soup) + table_str
    # Outputs
    if html:
        with open(f'{fn}.html', 'w') as f:
            f.write(output)
    pdfkit.from_string(output, f'{fn}.pdf')

if __name__ == '__main__':
    # TESTER CODE
    fn = 'fncm-rc4_MVT.txt'
    with open(fn, 'r') as txt:
        df = content2df(txt.read())
        df2pdf('21.0.2', 'FNCM', '05-18-2022', df, 'fncm-namespace')
