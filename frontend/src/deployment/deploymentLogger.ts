import winston, { Logger } from 'winston';

const consoleTransport = new winston.transports.Console()
const myWinstonOptions = {
  levels: winston.config.syslog.levels,
  transports: [consoleTransport]
}

export const logger: Logger = new (winston.createLogger as any)(myWinstonOptions);
