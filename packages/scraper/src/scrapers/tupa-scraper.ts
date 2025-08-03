import puppeteer from 'puppeteer';
import * as cheerio from 'cheerio';
import axios from 'axios';
import { logger } from '../utils/logger';

interface TramiteInfo {
  nombre: string;
  descripcion: string;
  requisitos: string[];
  pasos: string[];
  costo: number | null;
  duracion: string;
  urlOficial: string;
  entidad: string;
  esEnLinea: boolean;
  categoria: string;
  tags: string[];
}

export class TupaScraper {
  private browser: puppeteer.Browser | null = null;

  async init(): Promise<void> {
    try {
      this.browser = await puppeteer.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu',
        ],
      });
      logger.info('Navegador Puppeteer iniciado');
    } catch (error) {
      logger.error('Error iniciando navegador:', error);
      throw error;
    }
  }

  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      logger.info('Navegador cerrado');
    }
  }

  // Scraper principal para gob.pe
  async scrapeGobPe(): Promise<TramiteInfo[]> {
    if (!this.browser) {
      throw new Error('Navegador no iniciado');
    }

    const tramites: TramiteInfo[] = [];
    const page = await this.browser.newPage();

    try {
      // Configurar user agent
      await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36');
      
      // Ir a la página de trámites
      await page.goto('https://www.gob.pe/busquedas?contenido[]=tramites', {
        waitUntil: 'networkidle2',
        timeout: 30000,
      });

      logger.info('Navegando por gob.pe...');

      // Esperar a que carguen los resultados
      await page.waitForSelector('.search-result', { timeout: 10000 });

      // Obtener enlaces de trámites
      const tramiteLinks = await page.evaluate(() => {
        const links: string[] = [];
        const elements = document.querySelectorAll('.search-result h3 a');
        elements.forEach(el => {
          const href = el.getAttribute('href');
          if (href && href.includes('/tramites/')) {
            links.push('https://www.gob.pe' + href);
          }
        });
        return links.slice(0, 20); // Limitar a 20 trámites por ejecución
      });

      logger.info(`Encontrados ${tramiteLinks.length} enlaces de trámites`);

      // Procesar cada trámite
      for (const link of tramiteLinks) {
        try {
          const tramite = await this.scrapeTramiteDetail(link);
          if (tramite) {
            tramites.push(tramite);
            logger.info(`Scraped: ${tramite.nombre}`);
          }
        } catch (error) {
          logger.error(`Error scraping ${link}:`, error);
          continue;
        }
      }

    } catch (error) {
      logger.error('Error en scraping principal:', error);
    } finally {
      await page.close();
    }

    return tramites;
  }

  // Scraper de detalle de trámite individual
  private async scrapeTramiteDetail(url: string): Promise<TramiteInfo | null> {
    if (!this.browser) return null;

    const page = await this.browser.newPage();

    try {
      await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36');
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 20000 });

      const tramiteData = await page.evaluate(() => {
        const getTextContent = (selector: string): string => {
          const element = document.querySelector(selector);
          return element?.textContent?.trim() || '';
        };

        const getListItems = (selector: string): string[] => {
          const items: string[] = [];
          const elements = document.querySelectorAll(selector);
          elements.forEach(el => {
            const text = el.textContent?.trim();
            if (text) items.push(text);
          });
          return items;
        };

        // Extraer información básica
        const nombre = getTextContent('h1') || getTextContent('.tramite-title');
        const descripcion = getTextContent('.tramite-description') || 
                           getTextContent('.content-description') ||
                           getTextContent('p');

        // Extraer requisitos
        const requisitos = getListItems('.requisitos li') || 
                          getListItems('.requirements li') ||
                          getListItems('ul li').filter(item => 
                            item.toLowerCase().includes('requisito') ||
                            item.toLowerCase().includes('documento') ||
                            item.toLowerCase().includes('presentar')
                          );

        // Extraer pasos
        const pasos = getListItems('.pasos li') || 
                     getListItems('.steps li') ||
                     getListItems('ol li');

        // Buscar información de costo
        const costoText = getTextContent('.costo') || 
                         getTextContent('.cost') ||
                         document.body.innerHTML.match(/S\/\s*[\d,]+\.?\d*/)?.[0] || '';

        // Buscar duración
        const duracion = getTextContent('.duracion') || 
                        getTextContent('.duration') ||
                        getTextContent('.tiempo') ||
                        'No especificado';

        // Detectar si es en línea
        const contenido = document.body.textContent?.toLowerCase() || '';
        const esEnLinea = contenido.includes('en línea') || 
                         contenido.includes('online') ||
                         contenido.includes('virtual') ||
                         contenido.includes('digital');

        // Extraer entidad
        const entidad = getTextContent('.entidad') ||
                       getTextContent('.institution') ||
                       getTextContent('.organismo') ||
                       'No especificada';

        return {
          nombre,
          descripcion,
          requisitos,
          pasos,
          costoText,
          duracion,
          esEnLinea,
          entidad,
        };
      });

      // Procesar costo
      let costo: number | null = null;
      if (tramiteData.costoText) {
        const costoMatch = tramiteData.costoText.match(/[\d,]+\.?\d*/);
        if (costoMatch) {
          costo = parseFloat(costoMatch[0].replace(',', ''));
        }
      }

      // Determinar categoría basada en el contenido
      const categoria = this.determinarCategoria(tramiteData.nombre, tramiteData.descripcion);

      // Generar tags
      const tags = this.generarTags(tramiteData.nombre, tramiteData.descripcion);

      const tramite: TramiteInfo = {
        nombre: tramiteData.nombre,
        descripcion: tramiteData.descripcion,
        requisitos: tramiteData.requisitos,
        pasos: tramiteData.pasos,
        costo,
        duracion: tramiteData.duracion,
        urlOficial: url,
        entidad: tramiteData.entidad,
        esEnLinea: tramiteData.esEnLinea,
        categoria,
        tags,
      };

      return tramite;

    } catch (error) {
      logger.error(`Error scraping detalle de ${url}:`, error);
      return null;
    } finally {
      await page.close();
    }
  }

  // Determinar categoría del trámite
  private determinarCategoria(nombre: string, descripcion: string): string {
    const texto = (nombre + ' ' + descripcion).toLowerCase();

    const categorias = {
      'Identificación': ['dni', 'documento', 'identidad', 'cédula'],
      'Tributario': ['ruc', 'impuesto', 'tributo', 'sunat', 'fiscal'],
      'Empresarial': ['empresa', 'sociedad', 'constitución', 'comercial'],
      'Laboral': ['trabajo', 'empleo', 'laboral', 'contrato'],
      'Municipal': ['municipalidad', 'municipal', 'licencia', 'funcionamiento'],
      'Judicial': ['antecedentes', 'penales', 'judicial', 'certificado'],
      'Educativo': ['educación', 'título', 'grado', 'universidad'],
      'Salud': ['salud', 'médico', 'sanitario', 'hospital'],
      'Vehicular': ['vehículo', 'licencia', 'conducir', 'tránsito'],
      'Propiedad Intelectual': ['marca', 'patente', 'derecho', 'autor'],
    };

    for (const [categoria, palabras] of Object.entries(categorias)) {
      if (palabras.some(palabra => texto.includes(palabra))) {
        return categoria;
      }
    }

    return 'General';
  }

  // Generar tags relevantes
  private generarTags(nombre: string, descripcion: string): string[] {
    const texto = (nombre + ' ' + descripcion).toLowerCase();
    const tags: string[] = [];

    const palabrasClave = [
      'dni', 'ruc', 'empresa', 'licencia', 'certificado', 'permiso',
      'registro', 'inscripción', 'renovación', 'duplicado', 'tramite',
      'documento', 'solicitud', 'autorización', 'constitución',
    ];

    palabrasClave.forEach(palabra => {
      if (texto.includes(palabra)) {
        tags.push(palabra);
      }
    });

    // Remover duplicados y limitar a 5 tags
    return [...new Set(tags)].slice(0, 5);
  }

  // Scraper específico para RENIEC
  async scrapeReniec(): Promise<TramiteInfo[]> {
    if (!this.browser) return [];

    const tramites: TramiteInfo[] = [];
    const page = await this.browser.newPage();

    try {
      await page.goto('https://www.reniec.gob.pe/portal/tramitesServicios.htm', {
        waitUntil: 'networkidle2',
      });

      // Lógica específica para RENIEC
      // Esto sería más específico según la estructura de la página

    } catch (error) {
      logger.error('Error scraping RENIEC:', error);
    } finally {
      await page.close();
    }

    return tramites;
  }

  // Scraper específico para SUNAT
  async scrapeSunat(): Promise<TramiteInfo[]> {
    if (!this.browser) return [];

    const tramites: TramiteInfo[] = [];
    const page = await this.browser.newPage();

    try {
      await page.goto('https://www.sunat.gob.pe/orientacion/mypes/', {
        waitUntil: 'networkidle2',
      });

      // Lógica específica para SUNAT

    } catch (error) {
      logger.error('Error scraping SUNAT:', error);
    } finally {
      await page.close();
    }

    return tramites;
  }
}

// Función principal de scraping
export async function scrapeTramites(): Promise<TramiteInfo[]> {
  const scraper = new TupaScraper();
  
  try {
    await scraper.init();
    
    const [gobPeTramites, reniecTramites, sunatTramites] = await Promise.all([
      scraper.scrapeGobPe(),
      scraper.scrapeReniec(),
      scraper.scrapeSunat(),
    ]);

    const todosTramites = [
      ...gobPeTramites,
      ...reniecTramites,
      ...sunatTramites,
    ];

    logger.info(`Total de trámites scraped: ${todosTramites.length}`);
    return todosTramites;

  } catch (error) {
    logger.error('Error en scraping principal:', error);
    return [];
  } finally {
    await scraper.close();
  }
}

// Ejecutar scraper si es llamado directamente
if (require.main === module) {
  scrapeTramites()
    .then(tramites => {
      console.log('Trámites encontrados:', tramites.length);
      console.log(JSON.stringify(tramites, null, 2));
    })
    .catch(error => {
      console.error('Error:', error);
      process.exit(1);
    });
}
