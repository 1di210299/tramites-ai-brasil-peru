import winston from 'winston';

// Crear formato personalizado
const customFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.errors({ stack: true }),
  winston.format.printf(({ timestamp, level, message, stack, ...meta }) => {
    let log = `${timestamp} [${level.toUpperCase()}]: ${message}`;
    
    if (Object.keys(meta).length > 0) {
      log += ` ${JSON.stringify(meta)}`;
    }
    
    if (stack) {
      log += `\n${stack}`;
    }
    
    return log;
  })
);

// Configurar transports
const transports: winston.transport[] = [
  new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      customFormat
    )
  }),
  new winston.transports.File({
    filename: 'scraper.log',
    maxsize: 5242880, // 5MB
    maxFiles: 5,
  })
];

// Crear logger
export const logger = winston.createLogger({
  level: 'info',
  format: customFormat,
  transports,
  exceptionHandlers: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'scraper-exceptions.log' })
  ],
  rejectionHandlers: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'scraper-rejections.log' })
  ]
});
