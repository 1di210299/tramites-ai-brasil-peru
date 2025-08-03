import cron from 'node-cron';
import { scrapeTramites } from './scrapers/tupa-scraper';
import { logger } from './utils/logger';

// Configuración del cron job
// Se ejecuta todos los días a las 3:00 AM
const SCRAPING_SCHEDULE = '0 3 * * *';

function startScrapingCron() {
  logger.info('Iniciando sistema de scraping programado...');
  
  cron.schedule(SCRAPING_SCHEDULE, async () => {
    logger.info('🤖 Iniciando scraping programado de trámites...');
    
    try {
      const tramites = await scrapeTramites();
      
      if (tramites.length > 0) {
        // Aquí se guardarían los trámites en la base de datos
        // TODO: Implementar guardado en base de datos
        logger.info(`✅ Scraping completado: ${tramites.length} trámites encontrados`);
      } else {
        logger.warn('⚠️ No se encontraron trámites en el scraping');
      }
      
    } catch (error) {
      logger.error('❌ Error en scraping programado:', error);
    }
  }, {
    scheduled: true,
    timezone: 'America/Lima'
  });

  logger.info(`⏰ Cron job configurado para ejecutarse: ${SCRAPING_SCHEDULE} (horario de Lima)`);
}

// Ejecutar manualmente
async function runManualScraping() {
  logger.info('🚀 Ejecutando scraping manual...');
  
  try {
    const tramites = await scrapeTramites();
    logger.info(`✅ Scraping manual completado: ${tramites.length} trámites`);
    return tramites;
  } catch (error) {
    logger.error('❌ Error en scraping manual:', error);
    throw error;
  }
}

export { startScrapingCron, runManualScraping };

// Si se ejecuta directamente
if (require.main === module) {
  const command = process.argv[2];
  
  switch (command) {
    case 'start':
      startScrapingCron();
      logger.info('Sistema de scraping iniciado. Presiona Ctrl+C para detener.');
      break;
      
    case 'run':
      runManualScraping()
        .then(() => process.exit(0))
        .catch(() => process.exit(1));
      break;
      
    default:
      console.log('Comandos disponibles:');
      console.log('  npm run cron start  - Iniciar sistema de scraping programado');
      console.log('  npm run cron run    - Ejecutar scraping manual');
      process.exit(1);
  }
}
