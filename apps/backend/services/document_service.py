"""
Servicio para generación de documentos PDF
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from core.config import settings

class DocumentService:
    """Servicio para generación de documentos"""
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def generate_document(
        self,
        template_type: str,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Generar documento basado en plantilla"""
        
        # Crear directorio de usuario
        user_dir = os.path.join(self.upload_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Generar nombre único
        file_id = str(uuid.uuid4())
        filename = f"{template_type}_{file_id}.pdf"
        file_path = os.path.join(user_dir, filename)
        
        # Generar según tipo de plantilla
        if template_type == "solicitud_dni":
            await self._generate_dni_request(file_path, data)
        elif template_type == "solicitud_pasaporte":
            await self._generate_passport_request(file_path, data)
        elif template_type == "declaracion_jurada":
            await self._generate_sworn_statement(file_path, data)
        elif template_type == "poder_simple":
            await self._generate_simple_power(file_path, data)
        elif template_type == "solicitud_empresa":
            await self._generate_company_request(file_path, data)
        else:
            raise ValueError(f"Tipo de plantilla no soportado: {template_type}")
        
        # Obtener información del archivo
        file_size = os.path.getsize(file_path)
        
        return {
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": "application/pdf",
            "filename": filename
        }
    
    async def _generate_dni_request(self, file_path: str, data: Dict[str, Any]):
        """Generar solicitud de DNI"""
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centrado
        )
        
        story.append(Paragraph("SOLICITUD DE DOCUMENTO NACIONAL DE IDENTIDAD", title_style))
        story.append(Spacer(1, 20))
        
        # Información personal
        personal_info = [
            ["DATOS PERSONALES", ""],
            ["Nombres:", data.get("nombres", "")],
            ["Apellidos:", data.get("apellidos", "")],
            ["Fecha de Nacimiento:", data.get("fecha_nacimiento", "")],
            ["Lugar de Nacimiento:", data.get("lugar_nacimiento", "")],
            ["Dirección:", data.get("direccion", "")],
            ["Teléfono:", data.get("telefono", "")],
            ["Email:", data.get("email", "")]
        ]
        
        table = Table(personal_info, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Declaración
        declaration = f"""
        Declaro bajo juramento que los datos consignados en la presente solicitud son verdaderos.
        Asimismo, me comprometo a comunicar cualquier cambio que se produzca en los mismos.
        
        Fecha: {datetime.now().strftime('%d de %B de %Y')}
        
        
        _____________________________
        Firma del solicitante
        {data.get('nombres', '')} {data.get('apellidos', '')}
        """
        
        story.append(Paragraph(declaration, styles['Normal']))
        
        doc.build(story)
    
    async def _generate_passport_request(self, file_path: str, data: Dict[str, Any]):
        """Generar solicitud de pasaporte"""
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        story.append(Paragraph("SOLICITUD DE PASAPORTE PERUANO", title_style))
        story.append(Spacer(1, 20))
        
        # Información del solicitante
        info_data = [
            ["DATOS DEL SOLICITANTE", ""],
            ["Nombres:", data.get("nombres", "")],
            ["Apellidos:", data.get("apellidos", "")],
            ["DNI:", data.get("dni", "")],
            ["Teléfono:", data.get("telefono", "")],
            ["Email:", data.get("email", "")],
            ["Motivo del viaje:", data.get("motivo_viaje", "")]
        ]
        
        table = Table(info_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Requisitos
        requirements = """
        REQUISITOS:
        • Original y copia del DNI vigente
        • Recibo de pago por derecho de trámite
        • Fotografía actual a color
        • En caso de menores de edad, autorización de ambos padres
        """
        
        story.append(Paragraph(requirements, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Firma
        signature = f"""
        Fecha: {datetime.now().strftime('%d de %B de %Y')}
        
        
        _____________________________
        Firma del solicitante
        """
        
        story.append(Paragraph(signature, styles['Normal']))
        
        doc.build(story)
    
    async def _generate_sworn_statement(self, file_path: str, data: Dict[str, Any]):
        """Generar declaración jurada"""
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        story.append(Paragraph("DECLARACIÓN JURADA", title_style))
        story.append(Spacer(1, 30))
        
        # Contenido de la declaración
        declaration_text = f"""
        Yo, {data.get('nombres', '')} {data.get('apellidos', '')}, identificado(a) con DNI N° {data.get('dni', '')}, 
        declaro bajo juramento que:
        
        {data.get('declaracion', '')}
        
        La presente declaración la formulo en mérito a lo dispuesto en el artículo 46° del Texto Único 
        Ordenado de la Ley N° 27444, Ley del Procedimiento Administrativo General, aprobado mediante 
        Decreto Supremo N° 004-2019-JUS.
        """
        
        story.append(Paragraph(declaration_text, styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Lugar y fecha
        location_date = f"""
        {data.get('lugar', 'Lima')}, {data.get('fecha', datetime.now().strftime('%d de %B de %Y'))}
        
        
        _____________________________
        Firma del declarante
        {data.get('nombres', '')} {data.get('apellidos', '')}
        DNI: {data.get('dni', '')}
        """
        
        story.append(Paragraph(location_date, styles['Normal']))
        
        doc.build(story)
    
    async def _generate_simple_power(self, file_path: str, data: Dict[str, Any]):
        """Generar poder simple"""
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        story.append(Paragraph("PODER SIMPLE", title_style))
        story.append(Spacer(1, 30))
        
        # Contenido del poder
        power_text = f"""
        Por el presente documento, yo {data.get('poderdante', '')}, identificado(a) con DNI N° {data.get('dni_poderdante', '')}, 
        otorgo poder amplio y suficiente a {data.get('apoderado', '')}, identificado(a) con DNI N° {data.get('dni_apoderado', '')}, 
        para que en mi nombre y representación pueda:
        
        {data.get('facultades', '')}
        
        El presente poder tendrá vigencia hasta su revocación expresa.
        """
        
        story.append(Paragraph(power_text, styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Firmas
        signatures = f"""
        Lima, {datetime.now().strftime('%d de %B de %Y')}
        
        
        _____________________________          _____________________________
        {data.get('poderdante', '')}                      {data.get('apoderado', '')}
        DNI: {data.get('dni_poderdante', '')}              DNI: {data.get('dni_apoderado', '')}
        PODERDANTE                             APODERADO
        """
        
        story.append(Paragraph(signatures, styles['Normal']))
        
        doc.build(story)
    
    async def _generate_company_request(self, file_path: str, data: Dict[str, Any]):
        """Generar solicitud de constitución de empresa"""
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        story.append(Paragraph("SOLICITUD DE CONSTITUCIÓN DE EMPRESA", title_style))
        story.append(Spacer(1, 20))
        
        # Datos de la empresa
        company_data = [
            ["DATOS DE LA EMPRESA", ""],
            ["Razón Social:", data.get("razon_social", "")],
            ["Tipo de Empresa:", data.get("tipo_empresa", "")],
            ["Capital Social:", f"S/ {data.get('capital', '')}"],
            ["Actividad Económica:", data.get("actividad_economica", "")],
            ["Número de Socios:", str(len(data.get("socios", [])))]
        ]
        
        table = Table(company_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Lista de socios
        if data.get("socios"):
            story.append(Paragraph("SOCIOS:", styles['Heading3']))
            for i, socio in enumerate(data.get("socios", []), 1):
                story.append(Paragraph(f"{i}. {socio}", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Declaración
        declaration = f"""
        Declaro bajo juramento que la información proporcionada es veraz y me comprometo a 
        cumplir con todas las obligaciones legales correspondientes.
        
        Lima, {datetime.now().strftime('%d de %B de %Y')}
        
        
        _____________________________
        Firma del representante legal
        """
        
        story.append(Paragraph(declaration, styles['Normal']))
        
        doc.build(story)
