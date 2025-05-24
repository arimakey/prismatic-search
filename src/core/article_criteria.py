from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from agents import api
from utils.file_utils import save_data_to_file
from utils.console_formatter import print_formatted_text

load_dotenv()
console = Console()

class StudyType(Enum):
    """Enumeration of available study types."""
    RCT = "Ensayos clínicos aleatorizados"
    NON_RCT = "Ensayos clínicos no aleatorizados"
    OBSERVATIONAL = "Estudios observacionales"
    COHORT = "Estudios de cohorte"
    CASE_CONTROL = "Estudios de casos y controles"
    CROSS_SECTIONAL = "Estudios transversales"
    SYSTEMATIC_REVIEWS = "Revisiones sistemáticas"
    META_ANALYSIS = "Meta-análisis"
    QUALITATIVE = "Estudios cualitativos"

class PopulationType(Enum):
    """Enumeration of population types."""
    ADULTS = "Adultos (18+ años)"
    CHILDREN = "Niños y adolescentes (<18 años)"
    ALL_AGES = "Ambos (todas las edades)"
    SPECIFIC = "Poblaciones específicas (se te pedirá especificar)"

@dataclass
class CriteriaConfiguration:
    """Data class to store criteria generation configuration."""
    title: str
    population: str
    study_types: List[str]
    min_year: str
    max_year: str
    languages: List[str]
    exclusion_criteria: List[str]
    methodological_requirements: List[str]
    additional_criteria: str
    context: str

@dataclass
class ParsedCriteria:
    """Data class to store parsed criteria sections."""
    inclusion: str
    exclusion: str
    filters: str

class CriteriaParser:
    """Class responsible for parsing and formatting generated content."""
    
    SECTION_KEYWORDS = {
        "inclusion": ["criterios de inclusión", "inclusion criteria"],
        "exclusion": ["criterios de exclusión", "exclusion criteria"], 
        "filters": ["filtros metodológicos", "filtros explícitos", "methodological filters"]
    }
    
    @staticmethod
    def parse_generated_content(content: str) -> ParsedCriteria:
        """
        Parse and format generated content, removing double formatting and improving indentation.
        
        Args:
            content: Raw generated content string
            
        Returns:
            ParsedCriteria object with formatted sections
        """
        sections = {"inclusion": "", "exclusion": "", "filters": ""}
        current_section = None
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Identify sections based on keywords
            section_detected = CriteriaParser._detect_section(line.lower())
            if section_detected:
                current_section = section_detected
                continue

            if current_section and current_section in sections:
                # Clean the line from markdown formatting
                clean_line = CriteriaParser._clean_markdown(line)
                formatted_line = CriteriaParser._format_content_line(clean_line)
                
                if formatted_line:
                    if sections[current_section]:
                        sections[current_section] += "\n" + formatted_line
                    else:
                        sections[current_section] = formatted_line

        return ParsedCriteria(
            inclusion=sections["inclusion"],
            exclusion=sections["exclusion"], 
            filters=sections["filters"]
        )
    
    @staticmethod
    def _detect_section(line_lower: str) -> Optional[str]:
        """Detect which section a line belongs to based on keywords."""
        for section, keywords in CriteriaParser.SECTION_KEYWORDS.items():
            if any(keyword in line_lower for keyword in keywords):
                return section
        return None
    
    @staticmethod
    def _clean_markdown(line: str) -> str:
        """Remove markdown formatting from line."""
        # Remove bold markdown formatting
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        # Remove italic markdown formatting  
        line = re.sub(r'\*(.*?)\*', r'\1', line)
        # Remove extra spaces
        line = re.sub(r'\s+', ' ', line).strip()
        return line
    
    @staticmethod
    def _format_content_line(line: str) -> str:
        """Format content lines for better display."""
        # Skip empty lines or separators
        if not line or line in ['-', '─', '|']:
            return ""
            
        # Handle numbered items with colons (section headers)
        if re.match(r'^\d+\.\s*.*:', line):
            parts = line.split(':', 1)
            if len(parts) == 2:
                title = re.sub(r'^\d+\.\s*', '', parts[0]).strip()
                content = parts[1].strip()
                return f"[bold cyan]{title}:[/bold cyan] {content}"
            else:
                title = re.sub(r'^\d+\.\s*', '', parts[0]).strip()
                return f"[bold cyan]{title}[/bold cyan]"
        
        # Handle numbered items without colons
        elif re.match(r'^\d+\.\s*', line):
            content = re.sub(r'^\d+\.\s*', '', line).strip()
            return f"• {content}"
        
        # Handle bullet points
        elif line.startswith(('- ', '• ', '* ')):
            content = re.sub(r'^[•\-\*]\s*', '', line).strip()
            return f"  - {content}"
        
        # Handle indented content
        elif line.startswith(('  ', '\t')):
            return f"  {line.strip()}"
        
        # Regular content
        else:
            return line

class CriteriaGenerator:
    """Main class for generating systematic review criteria."""
    
    DEFAULT_EXCLUSION_CRITERIA = [
        "Estudios en animales",
        "Estudios in vitro", 
        "Artículos sin resumen disponible",
        "Cartas al editor, comentarios y editoriales",
        "Protocolos de estudio sin resultados",
        "Estudios de caso único",
        "Literatura gris"
    ]
    
    DEFAULT_METHODOLOGICAL_REQUIREMENTS = [
        "Accesibilidad de texto completo",
        "Rigor científico verificable", 
        "Metodología explícita",
        "Resultados cuantitativos",
        "Resultados cualitativos"
    ]
    
    DEFAULT_LANGUAGES = ["Inglés", "Español", "Portugués", "Francés", "Alemán", "Italiano"]
    
    def __init__(self):
        self.parser = CriteriaParser()
    
    def collect_user_input(self, title: str, context_additional: str) -> CriteriaConfiguration:
        """
        Collect comprehensive user input for criteria generation.
        
        Args:
            title: Research title
            context_additional: Additional context
            
        Returns:
            CriteriaConfiguration object with all user inputs
        """
        console.print(Panel.fit(
            f"[bold blue]Configuración de Criterios para: {title}[/bold blue]",
            border_style="blue"
        ))
        
        # Population selection
        population = self._get_population_selection()
        
        # Study types
        study_types = self._get_study_types_selection()
        
        # Temporal range
        min_year, max_year = self._get_temporal_range()
        
        # Languages
        languages = self._get_languages_selection()
        
        # Exclusion criteria
        exclusion_criteria = self._get_exclusion_criteria()
        
        # Methodological requirements
        methodological_requirements = self._get_methodological_requirements()
        
        # Additional criteria
        additional_criteria = questionary.text(
            "Criterios adicionales específicos para esta revisión (opcional):"
        ).ask() or ""
        
        return CriteriaConfiguration(
            title=title,
            population=population,
            study_types=study_types,
            min_year=min_year,
            max_year=max_year,
            languages=languages,
            exclusion_criteria=exclusion_criteria,
            methodological_requirements=methodological_requirements,
            additional_criteria=additional_criteria.strip(),
            context=context_additional
        )
    
    def _get_population_selection(self) -> str:
        """Get population selection from user."""
        population = questionary.select(
            "¿Qué población objetivo desea estudiar?",
            choices=[pop.value for pop in PopulationType]
        ).ask()
        
        if population == PopulationType.SPECIFIC.value:
            population_detail = questionary.text(
                "Describa la población específica:"
            ).ask() or ""
            return f"Población específica: {population_detail.strip()}"
        
        return population
    
    def _get_study_types_selection(self) -> List[str]:
        """Get study types selection from user."""
        return questionary.checkbox(
            "Seleccione los tipos de estudios que desea incluir:",
            choices=[study_type.value for study_type in StudyType]
        ).ask() or []
    
    def _get_temporal_range(self) -> Tuple[str, str]:
        """Get temporal range from user input."""
        min_year = questionary.text(
            "Año mínimo de publicación (Ej: 2015):"
        ).ask() or "Sin restricción"
        
        max_year = questionary.text(
            "Año máximo de publicación (dejar vacío para presente):"
        ).ask() or "Presente"
        
        return min_year.strip(), max_year.strip()
    
    def _get_languages_selection(self) -> List[str]:
        """Get languages selection from user."""
        language_choices = self.DEFAULT_LANGUAGES + ["Otros"]
        languages = questionary.checkbox(
            "Seleccione los idiomas permitidos:",
            choices=language_choices
        ).ask() or []
        
        if "Otros" in languages:
            languages.remove("Otros")
            other_languages = questionary.text(
                "Especifique otros idiomas (separados por comas):"
            ).ask() or ""
            
            additional_langs = [
                lang.strip() for lang in other_languages.split(",") 
                if lang.strip()
            ]
            languages.extend(additional_langs)
        
        return languages
    
    def _get_exclusion_criteria(self) -> List[str]:
        """Get exclusion criteria selection from user."""
        return questionary.checkbox(
            "Seleccione criterios específicos de exclusión:",
            choices=self.DEFAULT_EXCLUSION_CRITERIA
        ).ask() or []
    
    def _get_methodological_requirements(self) -> List[str]:
        """Get methodological requirements from user."""
        return questionary.checkbox(
            "Requisitos metodológicos importantes:",
            choices=self.DEFAULT_METHODOLOGICAL_REQUIREMENTS
        ).ask() or []
    
    def generate_ai_prompt(self, config: CriteriaConfiguration) -> str:
        """
        Generate a comprehensive prompt for AI criteria generation.
        
        Args:
            config: Configuration object with user inputs
            
        Returns:
            Formatted prompt string
        """
        return (
            f"Título: {config.title}. "
            f"Población: {config.population}. "
            f"Tipos de estudio: {', '.join(config.study_types)}. "
            f"Rango temporal: {config.min_year} a {config.max_year}. "
            f"Idiomas: {', '.join(config.languages)}. "
            f"Criterios de exclusión: {', '.join(config.exclusion_criteria)}. "
            f"Requisitos metodológicos: {', '.join(config.methodological_requirements)}. "
            f"Criterios adicionales: {config.additional_criteria}. "
            f"Contexto: {config.context}."
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for AI generation."""
        return (
            "Eres un asistente experto en metodología científica especializado en revisiones sistemáticas. "
            "Genera criterios de inclusión y exclusión estructurados, precisos y académicos para una revisión sistemática "
            "basándote en la información proporcionada.\n\n"
            "FORMATO REQUERIDO:\n"
            "Organiza tu respuesta en exactamente tres secciones con estos títulos:\n"
            "1. 'Criterios de inclusión'\n"
            "2. 'Criterios de exclusión'\n"
            "3. 'Filtros metodológicos'\n\n"
            "REGLAS DE FORMATO:\n"
            "- NO uses formato markdown (**texto** o *texto*)\n"
            "- Usa numeración secuencial (1., 2., 3., etc.) para elementos principales\n"
            "- Usa guiones (-) para subelementos\n"
            "- Para títulos de categorías usa formato: '1. Título de categoría:'\n"
            "- Para elementos sin subcategorías usa formato: '1. Descripción del criterio'\n"
            "- Mantén un lenguaje académico preciso y específico\n"
            "- Asegúrate de que los criterios sean medibles y reproducibles\n\n"
            "EJEMPLO DE FORMATO CORRECTO:\n"
            "1. Población objetivo:\n"
            "- Adultos mayores de 18 años\n"
            "- Participantes con diagnóstico confirmado\n"
            "2. Tipos de estudio:\n"
            "- Ensayos clínicos aleatorizados\n"
            "- Estudios observacionales\n"
            "3. Criterio sin subcategorías"
        )
    
    def display_results(self, title: str, criteria: ParsedCriteria) -> None:
        """
        Display generated criteria in a formatted table.
        
        Args:
            title: Research title
            criteria: Parsed criteria object
        """
        # First show title
        console.print(Panel.fit(
            f"[bold blue]Criterios para Revisión Sistemática[/bold blue]\n[dim]{title}[/dim]",
            border_style="blue"
        ))
        
        # Display each section separately for better readability
        sections = [
            ("Criterios de Inclusión", criteria.inclusion, "green"),
            ("Criterios de Exclusión", criteria.exclusion, "red"), 
            ("Filtros Metodológicos", criteria.filters, "yellow")
        ]
        
        for section_title, content, color in sections:
            if content and content.strip():
                console.print(f"\n[bold {color}]═══ {section_title.upper()} ═══[/bold {color}]")
                console.print(Panel(
                    content,
                    border_style=color,
                    padding=(1, 2)
                ))
            else:
                console.print(f"\n[bold {color}]═══ {section_title.upper()} ═══[/bold {color}]")
                console.print(Panel(
                    "[dim italic]No se generaron criterios para esta sección[/dim italic]",
                    border_style=color,
                    padding=(1, 2)
                ))
    
    def generate_criteria(self, title: str, context_additional: str, project_name: str) -> Dict:
        """
        Main method to generate systematic review criteria.
        
        Args:
            title: Research title
            context_additional: Additional context
            project_name: Project name for file saving
            
        Returns:
            Dictionary with all generated criteria and configuration
        """
        try:
            # Collect user input
            config = self.collect_user_input(title, context_additional)
            
            # Generate AI conversation
            conversation = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": self.generate_ai_prompt(config)}
            ]
            
            # Show progress indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generando criterios...", total=None)
                generated_content = api.get_completion(conversation)
                progress.update(task, completed=True)
            
            # Save generated content
            save_data_to_file(project_name, "criteria.txt", generated_content)
            
            # Parse and display results
            parsed_criteria = self.parser.parse_generated_content(generated_content)
            self.display_results(title, parsed_criteria)
            
            # Show success message
            console.print(Panel.fit(
                "[green]✓ Criterios generados y guardados exitosamente[/green]",
                border_style="green"
            ))
            
            return {
                "titulo": config.title,
                "población": config.population,
                "tipos_estudio": config.study_types,
                "año_minimo": config.min_year,
                "año_maximo": config.max_year,
                "idiomas": config.languages,
                "criterios_exclusión": config.exclusion_criteria,
                "requisitos_metodológicos": config.methodological_requirements,
                "criterios_adicionales": config.additional_criteria,
                "criterios_generados": generated_content,
                "criterios_parseados": {
                    "inclusión": parsed_criteria.inclusion,
                    "exclusión": parsed_criteria.exclusion,
                    "filtros": parsed_criteria.filters
                }
            }
            
        except Exception as e:
            console.print(Panel.fit(
                f"[red]✗ Error al generar criterios: {str(e)}[/red]",
                border_style="red"
            ))
            raise

# Convenience function to maintain backwards compatibility
def generate_criteria(title: str, context_additional: str, project_name: str) -> Dict:
    """
    Generate criteria using the improved CriteriaGenerator class.
    
    Args:
        title: Research title
        context_additional: Additional context
        project_name: Project name for file saving
        
    Returns:
        Dictionary with generated criteria and configuration
    """
    generator = CriteriaGenerator()
    return generator.generate_criteria(title, context_additional, project_name)